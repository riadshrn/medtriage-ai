"""
Page Accueil - Regulation Agentique.

Cette page permet de sélectionner et analyser des conversations
patient-infirmier depuis la base de données de conversations.
"""

import os
import sys
from pathlib import Path

import requests
import streamlit as st

# Config Paths
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from state import init_session_state
from style import configure_page, apply_style, render_triage_badge, render_patient_card

init_session_state()
apply_style()
configure_page(page_title="Accueil - MedTriage-AI")

# URL de l'API Backend
API_URL = os.getenv("API_URL", "")

# Mapping des icônes (l'API renvoie des noms, on les convertit en emoji)
ICON_MAP = {
    "heart": "❤️",
    "stethoscope": "🩺",
    "foot": "🦶",
    "virus": "🤧",
    "brain": "🧠",
    "warning": "⚠️",
    "thermometer": "🌡️",
    "back": "🔙",
    "baby": "👶",
    "file": "📄"
}


def load_available_conversations():
    """Charge la liste des conversations depuis l'API."""
    try:
        response = requests.get(f"{API_URL}/conversation/list", timeout=10)
        if response.status_code == 200:
            conversations = response.json()
            # Convertir les icônes texte en emoji
            for conv in conversations:
                icon_name = conv.get("icon", "file")
                conv["icon"] = ICON_MAP.get(icon_name, "📄")
            return conversations
    except requests.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
    return []


def load_conversation_from_api(filename: str):
    """Charge une conversation depuis l'API."""
    try:
        response = requests.get(f"{API_URL}/conversation/load/{filename}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur: {response.text}")
    except requests.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
    return None


def save_triage_to_history(result: dict, filename: str, extracted_data: dict) -> str:
    """Sauvegarde le triage dans l'historique via l'API."""
    try:
        payload = {
            "source": "accueil",
            "filename": filename,
            "gravity_level": result.get("criticity", "GRIS"),
            "french_triage_level": result.get("french_triage_level"),
            "confidence_score": result.get("confidence_score"),
            "orientation": result.get("orientation"),
            "delai_prise_en_charge": result.get("delai_prise_en_charge"),
            "extracted_data": extracted_data,
            "model_version": result.get("model_version", "agent-v1"),
            "ml_available": True,
            "justification": result.get("justification"),
            "red_flags": result.get("red_flags"),
            "recommendations": result.get("recommendations")
        }
        response = requests.post(f"{API_URL}/history/save", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("prediction_id")
    except requests.RequestException as e:
        st.warning(f"Impossible de sauvegarder dans l'historique: {e}")
    return None


def main():
    if not API_URL:
        st.error("""
        **Configuration requise!**

        L'URL de l'API Backend n'est pas configurée.

        1. Déployez d'abord le Space Backend
        2. Copiez l'URL du Space Backend
        3. Ajoutez-la dans les secrets: `API_URL=https://votre-space.hf.space`
        """)
        st.stop()

    st.title("Accueil - Régulation Agentique")

    # Gestion de l'état
    if 'conversation_data' not in st.session_state:
        st.session_state['conversation_data'] = None
    if 'analysis_done' not in st.session_state:
        st.session_state['analysis_done'] = False
    if 'agent_result' not in st.session_state:
        st.session_state['agent_result'] = None
    if 'selected_conversation' not in st.session_state:
        st.session_state['selected_conversation'] = None
    if 'selected_conversation_info' not in st.session_state:
        st.session_state['selected_conversation_info'] = None

    # Charger les conversations disponibles
    conversations = load_available_conversations()

    # Section de sélection
    st.markdown("### Dossiers Patients Disponibles")
    st.caption("Sélectionnez une conversation pour l'analyser avec le copilote IA")

    if not conversations:
        st.warning("Aucune conversation trouvée dans le dossier.")

        # Option de fallback: upload manuel
        st.markdown("---")
        st.markdown("#### Upload manuel")
        uploaded_file = st.file_uploader("Chargez une transcription", type=["csv", "txt"])
        if uploaded_file:
            with st.spinner("Lecture du fichier..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                    res = requests.post(f"{API_URL}/conversation/upload", files=files, timeout=30)
                    if res.status_code == 200:
                        st.session_state['conversation_data'] = res.json()
                        st.session_state['current_filename'] = uploaded_file.name
                        st.session_state['analysis_done'] = False
                        st.session_state['agent_result'] = None
                        st.rerun()
                    else:
                        st.error(f"Erreur API: {res.text}")
                except Exception as e:
                    st.error(f"Erreur: {e}")
    else:
        # Afficher les conversations sous forme de cartes
        cols = st.columns(3)

        for idx, conv in enumerate(conversations):
            col = cols[idx % 3]
            with col:
                # Déterminer si cette conversation est sélectionnée
                is_selected = st.session_state.get('selected_conversation') == conv['filename']

                # Utiliser le nouveau composant de carte patient
                st.markdown(
                    render_patient_card(
                        icon=conv['icon'],
                        title=conv['name'],
                        level=conv['niveau'],
                        selected=is_selected
                    ),
                    unsafe_allow_html=True
                )

                if st.button(
                    "Sélectionner" if not is_selected else "✓ Sélectionné",
                    key=f"select_{conv['filename']}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    # Charger la conversation via l'API
                    data = load_conversation_from_api(conv['filename'])
                    if data:
                        st.session_state['conversation_data'] = data
                        st.session_state['current_filename'] = conv['filename']
                        st.session_state['selected_conversation'] = conv['filename']
                        st.session_state['selected_conversation_info'] = conv  # Stocker les infos (name, niveau, icon)
                        st.session_state['analysis_done'] = False
                        st.session_state['agent_result'] = None
                        st.rerun()

    # Interface principale si une conversation est chargée
    if st.session_state['conversation_data'] is not None:
        json_payload = st.session_state['conversation_data']

        st.markdown("---")

        # Info sur la conversation sélectionnée
        conv_info = st.session_state.get('selected_conversation_info')
        if conv_info:
            st.info(f"{conv_info.get('icon', '📄')} **{conv_info.get('name', 'Conversation')}** - Niveau attendu: {conv_info.get('niveau', 'N/A')}")

        label_expander = f"Replay: {st.session_state.get('current_filename', 'Discussion')}"
        is_expanded = not st.session_state['analysis_done']

        with st.expander(label_expander, expanded=is_expanded):
            chat_container = st.container(height=300, border=True)
            with chat_container:
                for msg in json_payload["messages"]:
                    avatar = "🧑‍⚕️" if msg["role"] == "infirmier" else "🤒"
                    role_style = "user" if msg["role"] == "infirmier" else "assistant"
                    with st.chat_message(role_style, avatar=avatar):
                        st.write(msg['content'])

        if not st.session_state['analysis_done']:
            st.markdown("---")
            if st.button("Lancer le Copilote", type="primary", use_container_width=True):
                with st.spinner("Analyse clinique en cours..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/conversation/agent-audit",
                            json=json_payload,
                            timeout=120
                        )
                        if response.status_code == 200:
                            res = response.json()
                            st.session_state['agent_result'] = res
                            st.session_state['last_agent_audit'] = res
                            st.session_state['triage_color'] = res.get("criticity", "GRIS")
                            st.session_state['analysis_done'] = True

                            # Ajout à l'historique pour les stats du Dashboard
                            criticity = res.get("criticity", "GRIS")
                            st.session_state['triage_history'].append(criticity)

                            # Stocker les métriques pour les totaux
                            m = res.get('metrics', {})
                            if m:
                                st.session_state['metrics_history'].append({
                                    'cost_usd': m.get('cost_usd', 0),
                                    'gwp_kgco2': m.get('gwp_kgco2', 0),
                                    'energy_kwh': m.get('energy_kwh', 0)
                                })
                                # Mettre à jour la dernière requête (toutes sources)
                                st.session_state['last_request_metrics'] = m
                                st.session_state['last_request_source'] = "Accueil"

                            # Sauvegarder dans l'historique
                            current_filename = st.session_state.get('current_filename', 'unknown')
                            extracted = res.get('extracted_data', {})
                            prediction_id = save_triage_to_history(res, current_filename, extracted)

                            # Stocker pour le feedback
                            st.session_state['last_triage_result'] = {
                                'prediction_id': prediction_id or f"pred_{current_filename}",
                                'gravity_level': res.get('criticity', 'GRIS'),
                                'french_triage_level': res.get('french_triage_level', 'Tri 5'),
                                'extracted_data': extracted,
                                'filename': current_filename,
                                'source': 'accueil'
                            }

                            st.rerun()
                        else:
                            st.error(f"Erreur API: {response.text}")
                    except requests.exceptions.Timeout:
                        st.error("Timeout - Réessayez")
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        if st.session_state['analysis_done'] and st.session_state['agent_result']:
            res = st.session_state['agent_result']
            extracted = res.get("extracted_data", {})
            constantes = extracted.get('constantes', {}) if extracted else {}
            alert = res.get("protocol_alert")
            missing_info = res.get("missing_info", [])
            criticity = st.session_state.get('triage_color', 'GRIS')

            st.divider()
            col_data, col_decision = st.columns([1, 1])

            with col_data:
                st.subheader("Données Structurées")
                m1, m2, m3 = st.columns(3)
                with m1:
                    douleur = constantes.get('echelle_douleur')
                    st.metric("Douleur", f"{douleur}/10" if douleur is not None else "-")
                with m2:
                    temp = constantes.get('temperature')
                    st.metric("Température", f"{temp}°C" if temp else "-")
                with m3:
                    age = extracted.get('age')
                    st.metric("Âge", f"{age} ans" if age else "-")

                with st.expander("Dossier complet", expanded=True):
                    st.json(extracted)

            with col_decision:
                st.subheader("Copilote IA")

                # Utiliser le nouveau badge de triage avec animation
                st.markdown(render_triage_badge(criticity), unsafe_allow_html=True)

                if alert:
                    st.error(f"**ALERTE PROTOCOLE**\n\n{alert}")
                else:
                    st.success("Aucun indicateur de gravité immédiate.")

                if missing_info:
                    st.warning("**Informations à demander:**")
                    for q in missing_info:
                        st.markdown(f"- {q}")
                elif not alert:
                    st.info("Dossier complet pour le triage.")

                st.markdown("---")
                with st.expander("Logs & Raisonnement"):
                    steps = res.get("reasoning_steps", [])
                    if steps:
                        for step in steps:
                            st.markdown(step)
                    else:
                        st.caption("Analyse directe.")

            st.markdown("---")

            # Boutons d'action
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Nouvelle Analyse", use_container_width=True):
                    st.session_state['analysis_done'] = False
                    st.session_state['conversation_data'] = None
                    st.session_state['selected_conversation'] = None
                    st.session_state['selected_conversation_info'] = None
                    st.rerun()

            with col2:
                if st.button("Donner un Feedback", type="primary", use_container_width=True):
                    st.switch_page("pages/3_Feedback.py")

    else:
        st.info("Sélectionnez une conversation ci-dessus pour commencer l'analyse.")


if __name__ == "__main__":
    main()
