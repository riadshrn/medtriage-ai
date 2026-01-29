"""
Page Feedback - Validation et correction des triages.

Cette page permet aux infirmières de:
- Valider ou corriger les triages effectués
- Voir l'historique des triages
- Consulter les métriques de performance
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
from style import apply_style, render_triage_badge

# Initialisation
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://backend:8000")

# Constantes
GRAVITY_LEVELS = ["ROUGE", "JAUNE", "VERT", "GRIS"]
FRENCH_LEVELS = ["Tri 1", "Tri 2", "Tri 3A", "Tri 3B", "Tri 4", "Tri 5"]
FEEDBACK_TYPES = {
    "correct": "Triage correct",
    "upgrade": "Sous-estimation (devrait être plus grave)",
    "downgrade": "Sur-estimation (devrait être moins grave)",
    "disagree": "Désaccord complet"
}


def get_triage_color(level: str) -> str:
    colors = {"ROUGE": "#dc3545", "JAUNE": "#ffc107", "VERT": "#28a745", "GRIS": "#6c757d"}
    return colors.get(level, "#6c757d")


def get_triage_emoji(level: str) -> str:
    emojis = {"ROUGE": "🔴", "JAUNE": "🟡", "VERT": "🟢", "GRIS": "⚪"}
    return emojis.get(level, "⚪")


def get_feedback_stats() -> Optional[Dict]:
    """Récupère les statistiques de feedback."""
    try:
        response = requests.get(f"{API_URL}/feedback/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_feedback_count() -> int:
    """Récupère le nombre de feedbacks."""
    try:
        response = requests.get(f"{API_URL}/feedback/count", timeout=5)
        if response.status_code == 200:
            return response.json().get("count", 0)
    except requests.RequestException:
        pass
    return 0


def get_triage_history(limit: int = 50) -> List[Dict]:
    """Récupère l'historique des triages depuis l'API."""
    try:
        response = requests.get(f"{API_URL}/history/list", params={"limit": limit}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("entries", [])
    except requests.RequestException:
        pass
    return []


def get_history_stats() -> Optional[Dict]:
    """Récupère les statistiques de l'historique."""
    try:
        response = requests.get(f"{API_URL}/history/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def update_history_feedback(prediction_id: str, feedback_type: str, corrected_gravity: Optional[str] = None) -> bool:
    """Met à jour le feedback dans l'historique."""
    try:
        params = {"feedback_type": feedback_type}
        if corrected_gravity:
            params["corrected_gravity"] = corrected_gravity
        response = requests.patch(
            f"{API_URL}/history/entry/{prediction_id}/feedback",
            params=params,
            timeout=10
        )
        return response.status_code == 200
    except requests.RequestException:
        pass
    return False


def submit_feedback(
    prediction_id: str,
    original_gravity: str,
    feedback_type: str,
    corrected_gravity: Optional[str] = None,
    corrected_french_level: Optional[str] = None,
    reason: Optional[str] = None,
    missed_symptoms: Optional[List[str]] = None,
    patient_features: Optional[Dict] = None,
    nurse_id: Optional[str] = None
) -> bool:
    """Soumet un feedback à l'API."""
    try:
        payload = {
            "prediction_id": prediction_id,
            "nurse_id": nurse_id or "anonymous",
            "original_gravity": original_gravity,
            "feedback_type": feedback_type,
            "corrected_gravity": corrected_gravity,
            "corrected_french_level": corrected_french_level,
            "reason": reason,
            "missed_symptoms": missed_symptoms or [],
            "patient_features": patient_features or {}
        }

        response = requests.post(
            f"{API_URL}/feedback/submit",
            json=payload,
            timeout=10
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def render_feedback_form() -> None:
    """Affiche le formulaire de feedback pour le dernier triage."""
    last_result = st.session_state.get('last_triage_result')

    if not last_result:
        st.info("Aucun triage récent à évaluer. Effectuez d'abord un triage depuis l'Accueil ou le Mode Interactif.")
        return

    st.markdown("## Évaluer le Triage")

    prediction_id = last_result.get('prediction_id', 'unknown')
    original_gravity = last_result.get('gravity_level', 'GRIS')
    french_level = last_result.get('french_triage_level', 'Tri 5')
    extracted_data = last_result.get('extracted_data', {})

    # Afficher le triage à évaluer
    emoji = get_triage_emoji(original_gravity)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            render_triage_badge(original_gravity, f"{emoji} {original_gravity} - {french_level}"),
            unsafe_allow_html=True
        )

    with col2:
        if extracted_data:
            st.markdown("**Données du patient:**")
            age = extracted_data.get('age')
            motif = extracted_data.get('motif_consultation')
            if age:
                st.write(f"- Âge: {age} ans")
            if motif:
                st.write(f"- Motif: {motif}")

    st.markdown("---")

    # Formulaire de feedback
    st.markdown("### Votre évaluation")

    # ID infirmier (optionnel)
    nurse_id = st.text_input("Votre identifiant (optionnel)", placeholder="Ex: IDE_42")

    # Type de feedback
    feedback_type = st.radio(
        "Le triage est-il correct ?",
        options=list(FEEDBACK_TYPES.keys()),
        format_func=lambda x: FEEDBACK_TYPES[x],
        horizontal=True
    )

    corrected_gravity = None
    corrected_french = None
    reason = None
    missed_symptoms = []

    # Si correction nécessaire
    if feedback_type in ["upgrade", "downgrade", "disagree"]:
        st.markdown("### Correction proposée")

        col1, col2 = st.columns(2)
        with col1:
            corrected_gravity = st.selectbox(
                "Niveau de gravité correct",
                options=GRAVITY_LEVELS,
                index=GRAVITY_LEVELS.index(original_gravity) if original_gravity in GRAVITY_LEVELS else 0
            )
        with col2:
            corrected_french = st.selectbox(
                "Niveau FRENCH correct",
                options=FRENCH_LEVELS
            )

        reason = st.text_area(
            "Raison de la correction",
            placeholder="Expliquez pourquoi le triage initial était incorrect..."
        )

        # Symptômes manqués
        missed_input = st.text_input(
            "Symptômes ou signes manqués (séparés par des virgules)",
            placeholder="Ex: dyspnée, tirage intercostal, cyanose"
        )
        if missed_input:
            missed_symptoms = [s.strip() for s in missed_input.split(",") if s.strip()]

    # Bouton de soumission
    st.markdown("---")

    if st.button("Soumettre le Feedback", type="primary", use_container_width=True):
        # Préparer les features du patient pour le retraining
        patient_features = {}
        if extracted_data:
            patient_features = {
                "age": extracted_data.get("age"),
                "sexe": extracted_data.get("sexe"),
                "temperature": extracted_data.get("constantes", {}).get("temperature"),
                "frequence_cardiaque": extracted_data.get("constantes", {}).get("frequence_cardiaque"),
                "saturation_oxygene": extracted_data.get("constantes", {}).get("saturation_oxygene"),
                "pression_systolique": extracted_data.get("constantes", {}).get("pression_systolique"),
                "echelle_douleur": extracted_data.get("constantes", {}).get("echelle_douleur"),
            }

        success = submit_feedback(
            prediction_id=prediction_id,
            original_gravity=original_gravity,
            feedback_type=feedback_type,
            corrected_gravity=corrected_gravity,
            corrected_french_level=corrected_french,
            reason=reason,
            missed_symptoms=missed_symptoms,
            patient_features=patient_features,
            nurse_id=nurse_id if nurse_id else None
        )

        if success:
            # Mettre à jour aussi l'historique
            update_history_feedback(prediction_id, feedback_type, corrected_gravity)

            st.success("Feedback enregistré avec succès ! Merci pour votre contribution.")
            # Effacer le dernier résultat
            st.session_state['last_triage_result'] = None
            st.balloons()
        else:
            st.error("Erreur lors de l'enregistrement du feedback. Vérifiez la connexion à l'API.")


def render_history() -> None:
    """Affiche l'historique des triages."""
    st.markdown("## Historique des Triages")

    history = get_triage_history()

    if not history:
        st.info("Aucun triage enregistré pour le moment.")
        return

    # Trier par date décroissante
    history_sorted = sorted(
        history,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )[:20]  # Limiter à 20 derniers

    for idx, entry in enumerate(history_sorted):
        gravity = entry.get('gravity_level', 'GRIS')
        color = get_triage_color(gravity)
        emoji = get_triage_emoji(gravity)
        timestamp = entry.get('timestamp', 'N/A')
        prediction_id = entry.get('prediction_id', 'N/A')[:8]
        french_level = entry.get('french_triage_level', 'N/A')

        # Parser le timestamp si possible
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp_display = dt.strftime("%d/%m/%Y %H:%M")
        except:
            timestamp_display = timestamp[:19] if len(timestamp) > 19 else timestamp

        with st.expander(f"{emoji} {gravity} - {timestamp_display} (ID: {prediction_id}...)"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**Niveau:** {french_level}")
                confidence = entry.get('confidence_score', 0)
                st.markdown(f"**Confiance:** {confidence*100:.0f}%")

            with col2:
                if entry.get('orientation'):
                    st.markdown(f"**Orientation:** {entry['orientation']}")
                if entry.get('delai_prise_en_charge'):
                    st.markdown(f"**Délai:** {entry['delai_prise_en_charge']}")

            with col3:
                st.markdown(f"**Modèle:** {entry.get('model_version', 'N/A')}")
                if entry.get('ml_available'):
                    st.markdown("**ML:** Actif")

            # Bouton pour donner un feedback sur cet historique
            if not entry.get('feedback_given'):
                if st.button(f"Donner un feedback", key=f"fb_{idx}"):
                    st.session_state['last_triage_result'] = {
                        'prediction_id': entry.get('prediction_id'),
                        'gravity_level': gravity,
                        'french_triage_level': french_level,
                        'extracted_data': entry.get('extracted_data') or entry.get('patient_input', {})
                    }
                    st.rerun()
            else:
                feedback_type = entry.get('feedback_type', 'correct')
                st.success(f"Feedback donné: {FEEDBACK_TYPES.get(feedback_type, feedback_type)}")


def render_metrics() -> None:
    """Affiche les métriques de performance."""
    st.markdown("## Métriques de Performance")

    # D'abord essayer les stats de l'historique
    history_stats = get_history_stats()
    feedback_stats = get_feedback_stats()

    if history_stats:
        st.markdown("### Statistiques des Triages")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Triages", history_stats.get('total_triages', 0))
        with col2:
            by_gravity = history_stats.get('by_gravity', {})
            st.metric("ROUGE", by_gravity.get('ROUGE', 0))
        with col3:
            st.metric("JAUNE", by_gravity.get('JAUNE', 0))
        with col4:
            st.metric("VERT", by_gravity.get('VERT', 0))

        # Répartition par source
        st.markdown("---")
        st.markdown("### Répartition par Source")
        col1, col2, col3 = st.columns(3)

        by_source = history_stats.get('by_source', {})
        with col1:
            st.metric("Accueil", by_source.get('accueil', 0))
        with col2:
            st.metric("Simulation", by_source.get('simulation', 0))
        with col3:
            st.metric("Feedbacks Donnés", history_stats.get('feedbacks_given', 0))

    elif not feedback_stats:
        st.warning("Impossible de charger les statistiques de feedback. Vérifiez la connexion à l'API.")
        return

    # Section Feedback Stats si disponible
    if feedback_stats:
        st.markdown("---")
        st.markdown("### Statistiques des Feedbacks")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Prédictions",
                feedback_stats.get('total_predictions', 0),
                help="Nombre total de triages effectués"
            )

        with col2:
            st.metric(
                "Feedbacks Reçus",
                feedback_stats.get('total_feedback', 0),
                help="Nombre de feedbacks infirmiers"
            )

        with col3:
            accuracy = feedback_stats.get('accuracy_rate', 0) * 100
            st.metric(
                "Taux de Précision",
                f"{accuracy:.1f}%",
                help="Pourcentage de triages validés comme corrects"
            )

        with col4:
            feedback_count = get_feedback_count()
            st.metric(
                "Feedbacks pour Retraining",
                feedback_count,
                help="Feedbacks disponibles pour le retraining"
            )

        st.markdown("---")

        # Graphique des types de feedback
        st.markdown("### Répartition des Feedbacks")

        col1, col2 = st.columns(2)

        with col1:
            # Taux par type
            upgrade_rate = feedback_stats.get('upgrade_rate', 0) * 100
            downgrade_rate = feedback_stats.get('downgrade_rate', 0) * 100
            disagree_rate = feedback_stats.get('disagree_rate', 0) * 100
            correct_rate = 100 - upgrade_rate - downgrade_rate - disagree_rate

            import pandas as pd

            feedback_data = pd.DataFrame({
                'Type': ['Corrects', 'Sous-estimations', 'Sur-estimations', 'Désaccords'],
                'Pourcentage': [correct_rate, upgrade_rate, downgrade_rate, disagree_rate]
            })

            st.bar_chart(feedback_data.set_index('Type'))

        with col2:
            # Détail par niveau de gravité
            st.markdown("**Détail par niveau:**")

            by_gravity = feedback_stats.get('by_gravity_level', {})

        for level in GRAVITY_LEVELS:
            level_stats = by_gravity.get(level, {})
            total = level_stats.get('total', 0)
            correct = level_stats.get('correct', 0)

            if total > 0:
                rate = (correct / total) * 100
                emoji = get_triage_emoji(level)
                st.markdown(f"{emoji} **{level}**: {correct}/{total} corrects ({rate:.0f}%)")

    st.markdown("---")

    # Informations sur le modèle
    st.markdown("### Modèle Actuel")

    try:
        response = requests.get(f"{API_URL}/models/latest", timeout=5)
        if response.status_code == 200:
            model_info = response.json()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**Version:** {model_info.get('version', 'N/A')}")
            with col2:
                st.markdown(f"**Stage:** {model_info.get('stage', 'N/A')}")
            with col3:
                metrics = model_info.get('metrics', {})
                accuracy = metrics.get('accuracy', 0) * 100
                st.markdown(f"**Accuracy:** {accuracy:.1f}%")
        else:
            st.info("Informations du modèle non disponibles")
    except:
        st.info("Impossible de charger les informations du modèle")


def main() -> None:
    """Point d'entrée principal de la page Feedback."""
    st.title("Feedback & Métriques")
    st.caption("Validez les triages et consultez les performances du système")

    # Onglets
    tab1, tab2, tab3 = st.tabs(["Nouveau Feedback", "Historique", "Métriques"])

    with tab1:
        render_feedback_form()

    with tab2:
        render_history()

    with tab3:
        render_metrics()


if __name__ == "__main__":
    main()
