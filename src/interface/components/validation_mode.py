"""
Mode Validation : Interface pour la validation infirmière des prédictions

Ce mode permet aux infirmières de :
- Voir les prédictions récentes
- Valider ou corriger les prédictions
- Consulter les statistiques de performance
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


def render_validation_mode():
    """Rendu du mode validation infirmière"""

    st.header("Validation Infirmière")
    st.markdown("""
    Ce mode permet de **valider les prédictions** du système de triage.

    Votre feedback est utilisé pour :
    - Améliorer la précision du modèle
    - Identifier les cas où le système se trompe
    - Réentraîner automatiquement le modèle
    """)

    if not API_AVAILABLE:
        st.error("Le client API n'est pas disponible. Vérifiez que l'API backend est démarrée.")
        st.code("docker-compose -f docker-compose.new.yml up api", language="bash")
        return

    # Vérifier la connexion API
    client = get_api_client()
    health = client.health_check()

    if health.get("status") != "healthy":
        st.warning(f"API non disponible: {health.get('message', 'Erreur inconnue')}")
        st.info("L'API backend doit être lancée pour utiliser ce mode.")
        return

    # Tabs pour les différentes vues
    tab1, tab2, tab3 = st.tabs([
        "En attente de validation",
        "Statistiques",
        "Historique"
    ])

    with tab1:
        render_pending_validations(client)

    with tab2:
        render_feedback_stats(client)

    with tab3:
        render_validation_history(client)


def render_pending_validations(client):
    """Affiche les prédictions en attente de validation"""

    st.subheader("Prédictions en attente")

    # Récupérer les prédictions en attente
    try:
        pending = client.get_pending_validations(limit=20)
    except Exception as e:
        st.error(f"Erreur lors de la récupération: {e}")
        return

    if not pending:
        st.success("Aucune prédiction en attente de validation")
        return

    st.info(f"{len(pending)} prédiction(s) en attente")

    # Afficher chaque prédiction
    for pred in pending:
        with st.expander(
            f"#{pred['id']} - {pred['predicted_level']} - {pred['motif_consultation'][:50]}...",
            expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Patient**")
                st.write(f"- Âge: {pred['patient_age']} ans")
                st.write(f"- Sexe: {pred['patient_sexe']}")
                st.write(f"- Motif: {pred['motif_consultation']}")

            with col2:
                st.markdown("**Prédiction**")
                level_colors = {
                    "ROUGE": "red", "JAUNE": "orange",
                    "VERT": "green", "GRIS": "gray"
                }
                color = level_colors.get(pred['predicted_level'], "blue")
                st.markdown(f"Niveau: :{color}[**{pred['predicted_level']}**]")
                st.write(f"FRENCH: {pred['french_triage_level']}")
                st.write(f"Confiance: {pred['confidence_score']:.1%}")

            st.markdown("---")
            st.markdown("**Validation**")

            # Formulaire de validation
            col_v1, col_v2 = st.columns(2)

            with col_v1:
                validated_level = st.selectbox(
                    "Niveau correct",
                    options=["ROUGE", "JAUNE", "VERT", "GRIS"],
                    index=["ROUGE", "JAUNE", "VERT", "GRIS"].index(pred['predicted_level']),
                    key=f"level_{pred['id']}"
                )

            with col_v2:
                is_correct = validated_level == pred['predicted_level']
                st.write(f"La prédiction était {'correcte' if is_correct else 'incorrecte'}")

            notes = st.text_area(
                "Notes (optionnel)",
                key=f"notes_{pred['id']}",
                placeholder="Expliquez votre correction si nécessaire..."
            )

            if st.button("Valider", key=f"validate_{pred['id']}", type="primary"):
                try:
                    result = client.submit_feedback(
                        prediction_id=pred['id'],
                        validated_level=validated_level,
                        is_correct=is_correct,
                        notes=notes if notes else None
                    )
                    st.success(f"Validation enregistrée ! ({result['feedback_count_today']} feedbacks aujourd'hui)")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {e}")


def render_feedback_stats(client):
    """Affiche les statistiques de feedback"""

    st.subheader("Statistiques de Performance")

    # Sélection de la période
    days = st.selectbox("Période", options=[7, 14, 30, 90], index=2)

    try:
        stats = client.get_feedback_stats(days=days)
    except Exception as e:
        st.error(f"Erreur: {e}")
        return

    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total prédictions", stats['total_predictions'])

    with col2:
        st.metric("Validées", stats['total_validated'])

    with col3:
        st.metric(
            "Taux de validation",
            f"{stats['validation_rate']:.1%}"
        )

    with col4:
        st.metric(
            "Précision",
            f"{stats['accuracy_rate']:.1%}",
            help="% de prédictions correctes parmi les validées"
        )

    # Stats par niveau
    st.markdown("---")
    st.subheader("Performance par niveau")

    level_stats = stats.get('stats_by_level', {})
    if level_stats:
        data = []
        for level, s in level_stats.items():
            data.append({
                "Niveau": level,
                "Prédictions": s.get('predicted_count', 0),
                "Validées": s.get('validated_count', 0),
                "Précision": f"{s.get('accuracy', 0):.1%}" if s.get('accuracy') else "N/A"
            })

        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)

    # Matrice de confusion
    st.markdown("---")
    st.subheader("Matrice de confusion")
    st.caption("Prédiction (ligne) vs Validation (colonne)")

    confusion = stats.get('confusion_matrix', {})
    if confusion:
        levels = ["ROUGE", "JAUNE", "VERT", "GRIS"]
        matrix_data = []
        for pred_level in levels:
            row = {"Prédit": pred_level}
            for val_level in levels:
                row[val_level] = confusion.get(pred_level, {}).get(val_level, 0)
            matrix_data.append(row)

        df_confusion = pd.DataFrame(matrix_data)
        st.dataframe(df_confusion.set_index("Prédit"), use_container_width=True)


def render_validation_history(client):
    """Affiche l'historique des validations"""

    st.subheader("Historique des prédictions")

    try:
        predictions = client.get_recent_predictions(limit=50)
    except Exception as e:
        st.error(f"Erreur: {e}")
        return

    if not predictions:
        st.info("Aucune prédiction récente")
        return

    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        filter_level = st.multiselect(
            "Filtrer par niveau",
            options=["ROUGE", "JAUNE", "VERT", "GRIS"],
            default=[]
        )
    with col2:
        filter_validated = st.selectbox(
            "Statut validation",
            options=["Tous", "Validées", "Non validées"]
        )

    # Appliquer filtres
    filtered = predictions
    if filter_level:
        filtered = [p for p in filtered if p['predicted_level'] in filter_level]
    if filter_validated == "Validées":
        filtered = [p for p in filtered if p.get('validated', False)]
    elif filter_validated == "Non validées":
        filtered = [p for p in filtered if not p.get('validated', False)]

    # Afficher en tableau
    if filtered:
        df_data = []
        for p in filtered:
            df_data.append({
                "ID": p['id'],
                "Date": p['created_at'][:16] if 'created_at' in p else "N/A",
                "Âge": p['patient_age'],
                "Motif": p['motif_consultation'][:40] + "..." if len(p['motif_consultation']) > 40 else p['motif_consultation'],
                "Prédiction": p['predicted_level'],
                "FRENCH": p['french_triage_level'],
                "Confiance": f"{p['confidence_score']:.0%}",
                "Validé": "Oui" if p.get('validated', False) else "Non",
                "Correction": p.get('validated_level', '-')
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Aucune prédiction correspondant aux filtres")
