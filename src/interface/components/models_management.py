"""
Gestion des Modèles : Interface pour le versioning et réentraînement

Ce mode permet de :
- Voir les modèles disponibles
- Activer un modèle spécifique
- Lancer le réentraînement
- Comparer les performances
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import conditionnel du client API
try:
    from src.interface.api_client import get_api_client
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


def render_models_management():
    """Rendu de la page de gestion des modèles"""

    st.header("Gestion des Modèles ML")
    st.markdown("""
    Cette page permet de gérer les modèles de machine learning utilisés pour le triage.

    **Fonctionnalités :**
    - Voir les modèles entraînés et leurs métriques
    - Activer un modèle spécifique pour la production
    - Lancer le réentraînement sur les données de feedback
    - Suivre l'évolution des performances avec MLflow
    """)

    if not API_AVAILABLE:
        st.error("Le client API n'est pas disponible.")
        return

    client = get_api_client()
    health = client.health_check()

    if health.get("status") != "healthy":
        st.warning("API non disponible")
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "Modèles disponibles",
        "Réentraînement",
        "MLflow"
    ])

    with tab1:
        render_models_list(client)

    with tab2:
        render_retraining(client)

    with tab3:
        render_mlflow_info()


def render_models_list(client):
    """Affiche la liste des modèles"""

    st.subheader("Modèles enregistrés")

    try:
        models_data = client.get_models()
        active_model = client.get_active_model()
    except Exception as e:
        st.error(f"Erreur: {e}")
        return

    # Modèle actif
    st.markdown("### Modèle actif")

    if active_model and not active_model.get("using_default"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Version", active_model.get('version', 'N/A'))
        with col2:
            st.metric("Accuracy", f"{active_model.get('accuracy', 0):.1%}")
        with col3:
            st.metric("F1 Score", f"{active_model.get('f1_score', 0):.1%}")
        with col4:
            st.metric("Samples", active_model.get('training_samples', 'N/A'))
    else:
        st.info("Utilisation du modèle par défaut (non enregistré dans la base)")

    # Liste des modèles
    st.markdown("---")
    st.markdown("### Tous les modèles")

    models = models_data.get('models', [])

    if not models:
        st.info("Aucun modèle enregistré. Lancez un réentraînement pour créer le premier.")
        return

    for model in models:
        with st.expander(
            f"{'⭐ ' if model.get('is_active') else ''}{model.get('version', 'Unknown')} - "
            f"Accuracy: {model.get('accuracy', 0):.1%}",
            expanded=model.get('is_active', False)
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Informations**")
                st.write(f"- ID: {model.get('id')}")
                st.write(f"- Créé le: {model.get('created_at', 'N/A')[:16]}")
                st.write(f"- Samples d'entraînement: {model.get('training_samples', 'N/A')}")
                if model.get('mlflow_run_id'):
                    st.write(f"- MLflow Run: `{model.get('mlflow_run_id')[:8]}...`")

            with col2:
                st.markdown("**Métriques**")
                metrics = {
                    "Accuracy": model.get('accuracy'),
                    "Precision": model.get('precision_score'),
                    "Recall": model.get('recall_score'),
                    "F1 Score": model.get('f1_score')
                }
                for name, value in metrics.items():
                    if value is not None:
                        st.write(f"- {name}: {value:.2%}")

            if not model.get('is_active'):
                if st.button(f"Activer ce modèle", key=f"activate_{model.get('id')}"):
                    try:
                        result = client.activate_model(model.get('id'))
                        st.success(f"Modèle {model.get('version')} activé !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            else:
                st.success("Ce modèle est actuellement actif")


def render_retraining(client):
    """Interface de réentraînement"""

    st.subheader("Réentraînement du modèle")

    st.markdown("""
    Le réentraînement utilise les données de feedback validées par les infirmières
    pour améliorer le modèle.

    **Sources de données disponibles :**
    - Feedback infirmier (données corrigées)
    - Datasets Hugging Face (miriad, medical-cases-fr)
    """)

    # Récupérer les stats de feedback
    try:
        stats = client.get_feedback_stats(days=30)
        validated_count = stats.get('total_validated', 0)
    except Exception:
        validated_count = 0

    st.info(f"Données de feedback disponibles: {validated_count} prédictions validées")

    # Options de réentraînement
    st.markdown("---")
    st.markdown("### Configuration")

    col1, col2 = st.columns(2)

    with col1:
        use_feedback = st.checkbox(
            "Utiliser les données de feedback",
            value=True,
            help="Inclure les prédictions validées par les infirmières"
        )

        min_samples = st.number_input(
            "Minimum de samples requis",
            min_value=10,
            max_value=1000,
            value=100,
            help="Nombre minimum de feedbacks pour lancer l'entraînement"
        )

    with col2:
        use_hf = st.checkbox(
            "Utiliser les datasets Hugging Face",
            value=False,
            help="Inclure miriad et medical-cases-fr pour plus de données"
        )

        st.caption("""
        **Datasets HF disponibles:**
        - miriad/miriad-4.4M
        - mlabonne/medical-cases-fr
        """)

    # Vérification des prérequis
    st.markdown("---")

    can_train = True
    warnings = []

    if use_feedback and validated_count < min_samples:
        can_train = False
        warnings.append(f"Pas assez de feedbacks ({validated_count}/{min_samples})")

    if warnings:
        for w in warnings:
            st.warning(w)

    # Bouton de lancement
    if st.button(
        "Lancer le réentraînement",
        type="primary",
        disabled=not can_train
    ):
        with st.spinner("Réentraînement en cours..."):
            try:
                result = client.retrain_model(
                    use_feedback_data=use_feedback,
                    use_hf_datasets=use_hf,
                    min_feedback_samples=min_samples
                )

                if result.get('success'):
                    st.success(f"Réentraînement lancé ! {result.get('message')}")
                    if result.get('new_model_version'):
                        st.info(f"Nouvelle version: {result.get('new_model_version')}")
                else:
                    st.error(result.get('message', 'Erreur inconnue'))

            except Exception as e:
                st.error(f"Erreur: {e}")


def render_mlflow_info():
    """Affiche les informations MLflow"""

    st.subheader("MLflow Tracking")

    st.markdown("""
    MLflow est utilisé pour tracker les expériences de machine learning :
    - Métriques de chaque entraînement
    - Hyperparamètres utilisés
    - Artefacts (modèles, préprocesseurs)
    - Comparaison des versions
    """)

    st.markdown("---")

    st.markdown("### Accéder à l'interface MLflow")

    st.code("""
    # Lancer l'interface MLflow (local)
    docker-compose -f docker-compose.new.yml --profile mlflow up

    # Ou directement avec Python
    mlflow ui --backend-store-uri sqlite:///data/mlflow.db --port 5000
    """, language="bash")

    st.info("Une fois lancé, accédez à http://localhost:5000")

    st.markdown("---")

    st.markdown("### Structure des expériences")

    st.markdown("""
    Chaque entraînement est loggé avec :

    | Élément | Description |
    |---------|-------------|
    | **Paramètres** | n_estimators, max_depth, learning_rate... |
    | **Métriques** | accuracy, precision, recall, f1_score |
    | **Artefacts** | triage_model.json, preprocessor.pkl |
    | **Tags** | version, date, source_data |
    """)
