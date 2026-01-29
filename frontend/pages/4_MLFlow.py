"""
Page MLFlow - Gestion des modèles et retraining.

Cette page permet de:
- Voir les modèles enregistrés dans MLFlow
- Voir le nombre de feedbacks disponibles
- Lancer le retraining du modèle
- Promouvoir un modèle en production
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# Configuration des chemins
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from state import init_session_state
from style import apply_style, render_triage_badge, render_stage_badge, render_status_indicator

# Initialisation
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://backend:8000")

# Seuils
MIN_FEEDBACK_FOR_RETRAIN = 50


def get_models_list() -> Dict:
    """Récupère la liste des modèles depuis MLFlow."""
    try:
        response = requests.get(f"{API_URL}/models/list", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return {"versions": [], "total_versions": 0}


def get_latest_model() -> Optional[Dict]:
    """Récupère le modèle en production."""
    try:
        response = requests.get(f"{API_URL}/models/latest", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_model_version(version: int) -> Optional[Dict]:
    """Récupère les détails d'une version spécifique."""
    try:
        response = requests.get(f"{API_URL}/models/version/{version}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_experiments() -> List[Dict]:
    """Récupère la liste des expériences MLFlow."""
    try:
        response = requests.get(f"{API_URL}/models/experiments", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return []


def get_training_runs(experiment_name: str = None, limit: int = 10) -> Dict:
    """Récupère les runs d'entraînement."""
    try:
        params = {"limit": limit}
        if experiment_name:
            params["experiment_name"] = experiment_name

        response = requests.get(f"{API_URL}/models/runs", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return {"runs": []}


def get_feedback_count() -> int:
    """Récupère le nombre de feedbacks disponibles."""
    try:
        response = requests.get(f"{API_URL}/feedback/count", timeout=5)
        if response.status_code == 200:
            return response.json().get("count", 0)
    except requests.RequestException:
        pass
    return 0


def get_feedback_stats() -> Optional[Dict]:
    """Récupère les statistiques de feedback."""
    try:
        response = requests.get(f"{API_URL}/feedback/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def trigger_retrain() -> Optional[Dict]:
    """Lance le retraining du modèle."""
    try:
        response = requests.post(
            f"{API_URL}/feedback/retrain",
            json={"include_feedback": True, "min_feedback_samples": MIN_FEEDBACK_FOR_RETRAIN},
            timeout=300  # 5 minutes max
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}
    return None


def promote_model(version: int, stage: str) -> bool:
    """Promeut un modèle vers un stage."""
    try:
        response = requests.post(
            f"{API_URL}/models/promote/{version}",
            params={"stage": stage},
            timeout=30
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def render_current_model() -> None:
    """Affiche les informations du modèle actuel."""
    st.markdown("## Modèle en Production")

    latest = get_latest_model()

    if not latest:
        st.warning("Aucun modèle en production. Entraînez et promouvez un modèle.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        version = latest.get('version', 'N/A')
        st.metric("Version", f"v{version}")

    with col2:
        stage = latest.get('stage', 'None')
        st.markdown(render_stage_badge(stage), unsafe_allow_html=True)

    with col3:
        metrics = latest.get('metrics', {})
        accuracy = metrics.get('accuracy', 0) * 100
        st.metric("Accuracy", f"{accuracy:.1f}%")

    # Détails des métriques
    st.markdown("---")
    st.markdown("### Métriques du Modèle")

    metrics = latest.get('metrics', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        f1 = metrics.get('f1_macro', 0) * 100
        st.metric("F1 Score", f"{f1:.1f}%")

    with col2:
        precision = metrics.get('precision_macro', 0) * 100
        st.metric("Précision", f"{precision:.1f}%")

    with col3:
        recall = metrics.get('recall_macro', 0) * 100
        st.metric("Rappel", f"{recall:.1f}%")

    with col4:
        latency = metrics.get('latency_per_sample_ms', 0)
        st.metric("Latence", f"{latency:.1f} ms")

    # Tags et paramètres
    with st.expander("Détails techniques"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Paramètres:**")
            params = latest.get('params', {})
            for key, value in params.items():
                st.write(f"- {key}: {value}")

        with col2:
            st.markdown("**Tags:**")
            tags = latest.get('tags', {})
            for key, value in tags.items():
                st.write(f"- {key}: {value}")


def render_models_list() -> None:
    """Affiche la liste des modèles enregistrés."""
    st.markdown("## Versions de Modèles")

    models_data = get_models_list()
    versions = models_data.get('versions', [])

    if not versions:
        st.info("Aucun modèle enregistré dans MLFlow.")
        return

    # Trier par version décroissante
    models_sorted = sorted(versions, key=lambda x: x.get('version', 0), reverse=True)

    for model in models_sorted:
        version = model.get('version', 'N/A')
        stage = model.get('stage', 'None')
        metrics = model.get('metrics') or {}
        accuracy = (metrics.get('accuracy') or 0) * 100
        created = model.get('created_at', '')

        # Parser la date
        try:
            if created:
                if isinstance(created, str):
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(created / 1000)
                created_display = dt.strftime("%d/%m/%Y %H:%M")
            else:
                created_display = "N/A"
        except:
            created_display = str(created)[:19] if created else "N/A"

        # Couleur selon le stage
        stage_color = "#28a745" if stage == "Production" else "#ffc107" if stage == "Staging" else "#6c757d"
        stage_emoji = "🟢" if stage == "Production" else "🟡" if stage == "Staging" else "⚪"

        with st.expander(f"{stage_emoji} Version {version} - {stage} (Accuracy: {accuracy:.1f}%)"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**Créé le:** {created_display}")
                st.markdown(f"**Stage:** {stage}")

            with col2:
                st.markdown("**Métriques:**")
                st.write(f"- Accuracy: {accuracy:.1f}%")
                f1 = (metrics.get('f1_macro') or 0) * 100
                st.write(f"- F1: {f1:.1f}%")

            with col3:
                # Boutons de promotion
                st.markdown("**Actions:**")

                if stage != "Production":
                    if st.button("Promouvoir en Production", key=f"prod_{version}"):
                        if promote_model(version, "Production"):
                            st.success(f"Version {version} promue en Production !")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la promotion")

                if stage != "Staging" and stage != "Production":
                    if st.button("Mettre en Staging", key=f"staging_{version}"):
                        if promote_model(version, "Staging"):
                            st.success(f"Version {version} mise en Staging !")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la promotion")


def render_feedback_summary() -> None:
    """Affiche le résumé des feedbacks pour le retraining."""
    st.markdown("## Feedbacks pour Retraining")

    feedback_count = get_feedback_count()
    stats = get_feedback_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Feedbacks Disponibles",
            feedback_count,
            help="Nombre de corrections infirmières disponibles"
        )

    with col2:
        if stats:
            error_rate = (stats.get('upgrade_rate', 0) + stats.get('downgrade_rate', 0) + stats.get('disagree_rate', 0)) * 100
            st.metric(
                "Taux d'Erreur",
                f"{error_rate:.1f}%",
                delta=f"{-error_rate:.1f}% si objectif 0%",
                delta_color="inverse"
            )
        else:
            st.metric("Taux d'Erreur", "N/A")

    with col3:
        ready_for_retrain = feedback_count >= MIN_FEEDBACK_FOR_RETRAIN
        status_text = "Prêt pour retraining" if ready_for_retrain else f"Besoin de {MIN_FEEDBACK_FOR_RETRAIN - feedback_count} feedbacks"
        st.markdown(
            render_status_indicator(ready_for_retrain, status_text, status_text),
            unsafe_allow_html=True
        )

    # Détail des feedbacks
    if stats:
        st.markdown("---")
        st.markdown("### Répartition des Corrections")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            correct = stats.get('accuracy_rate', 0) * 100
            st.metric("Corrects", f"{correct:.0f}%")

        with col2:
            upgrade = stats.get('upgrade_rate', 0) * 100
            st.metric("Sous-estimations", f"{upgrade:.0f}%")

        with col3:
            downgrade = stats.get('downgrade_rate', 0) * 100
            st.metric("Sur-estimations", f"{downgrade:.0f}%")

        with col4:
            disagree = stats.get('disagree_rate', 0) * 100
            st.metric("Désaccords", f"{disagree:.0f}%")


def render_retrain_section() -> None:
    """Affiche la section de retraining."""
    st.markdown("## Lancer le Retraining")

    feedback_count = get_feedback_count()
    ready_for_retrain = feedback_count >= MIN_FEEDBACK_FOR_RETRAIN

    if not ready_for_retrain:
        st.warning(
            f"Pas assez de feedbacks pour lancer le retraining. "
            f"Minimum requis: {MIN_FEEDBACK_FOR_RETRAIN}, disponibles: {feedback_count}"
        )
        st.button("Lancer le Retraining", disabled=True, use_container_width=True)
        return

    st.success(f"{feedback_count} feedbacks disponibles - Retraining possible !")

    st.markdown("""
    **Le retraining va:**
    1. Charger les données d'entraînement originales
    2. Ajouter les corrections infirmières comme nouveaux exemples
    3. Entraîner un nouveau modèle avec validation croisée
    4. Enregistrer le modèle dans MLFlow
    """)

    if st.button("Lancer le Retraining", type="primary", use_container_width=True):
        with st.spinner("Retraining en cours... Cela peut prendre quelques minutes."):
            result = trigger_retrain()

            if result and result.get('status') == 'completed':
                st.success("Retraining terminé avec succès !")

                st.markdown("### Résultats")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Run ID:** `{result.get('mlflow_run_id', 'N/A')}`")
                    st.markdown(f"**Feedbacks utilisés:** {result.get('feedback_samples_used', 0)}")

                with col2:
                    st.markdown(f"**Message:** {result.get('message', '')}")

                st.balloons()
                st.info("Le nouveau modèle est disponible dans la liste des versions. Promouvez-le en Production pour l'utiliser.")

            elif result and result.get('status') == 'error':
                st.error(f"Erreur lors du retraining: {result.get('message', 'Erreur inconnue')}")
            else:
                st.error("Erreur lors du retraining. Vérifiez les logs du backend.")


def render_training_history() -> None:
    """Affiche l'historique des entraînements."""
    st.markdown("## Historique des Entraînements")

    runs_data = get_training_runs(limit=10)
    runs = runs_data.get('runs', []) if isinstance(runs_data, dict) else []

    if not runs:
        st.info("Aucun run d'entraînement trouvé.")
        return

    for run in runs:
        run_id = run.get('run_id', 'N/A')[:8]
        status = run.get('status', 'N/A')
        start_time = run.get('start_time', '')
        metrics = run.get('metrics') or {}
        tags = run.get('tags') or {}

        # Parser la date
        try:
            if start_time:
                if isinstance(start_time, str):
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(start_time / 1000)
                time_display = dt.strftime("%d/%m/%Y %H:%M")
            else:
                time_display = "N/A"
        except:
            time_display = str(start_time)[:19] if start_time else "N/A"

        # Emoji selon le status
        status_emoji = "✅" if status == "FINISHED" else "🔄" if status == "RUNNING" else "❌"

        # Trigger info
        trigger = tags.get('trigger', 'manual')
        trigger_emoji = "🔄" if trigger == "feedback" else "👤"

        accuracy = (metrics.get('accuracy') or 0) * 100

        with st.expander(f"{status_emoji} {time_display} - {trigger_emoji} {trigger} (Accuracy: {accuracy:.1f}%)"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Run ID:** `{run.get('run_id', 'N/A')}`")
                st.markdown(f"**Status:** {status}")
                st.markdown(f"**Trigger:** {trigger}")

                feedback_samples = tags.get('feedback_samples', '0')
                st.markdown(f"**Feedbacks utilisés:** {feedback_samples}")

            with col2:
                st.markdown("**Métriques:**")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        st.write(f"- {key}: {value*100:.1f}%")
                    else:
                        st.write(f"- {key}: {value}")


def main() -> None:
    """Point d'entrée principal de la page MLFlow."""
    st.title("MLFlow - Gestion des Modèles")
    st.caption("Gérez les versions de modèles et lancez le retraining")

    # Vérifier la connexion à l'API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            st.error("API Backend non disponible")
            return
    except:
        st.error("Impossible de se connecter à l'API Backend")
        return

    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "Modèle Actuel",
        "Versions",
        "Retraining",
        "Historique"
    ])

    with tab1:
        render_current_model()
        st.markdown("---")
        render_feedback_summary()

    with tab2:
        render_models_list()

    with tab3:
        render_feedback_summary()
        st.markdown("---")
        render_retrain_section()

    with tab4:
        render_training_history()


if __name__ == "__main__":
    main()
