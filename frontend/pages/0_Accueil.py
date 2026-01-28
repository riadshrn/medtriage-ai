import streamlit as st
import requests
import os
import sys
from pathlib import Path

# Config Paths
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

# URL de l'API Backend - Configurez dans les secrets HF Spaces
API_URL = os.getenv("API_URL", "")

if not API_URL:
    st.error("""
    **Configuration requise!**

    L'URL de l'API Backend n'est pas configuree.

    1. Deployez d'abord le Space Backend
    2. Copiez l'URL du Space Backend
    3. Ajoutez-la dans les secrets: `API_URL=https://votre-space.hf.space`
    """)
    st.stop()

st.title("Accueil - Regulation Agentique")
st.markdown("### Dossier Patient")

# Gestion de l'etat
if 'conversation_data' not in st.session_state:
    st.session_state['conversation_data'] = None
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
if 'agent_result' not in st.session_state:
    st.session_state['agent_result'] = None

# Upload
uploaded_file = st.file_uploader("Chargez la transcription", type=["csv", "txt"], key="uploader")

if uploaded_file is not None:
    if st.session_state.get('current_filename') != uploaded_file.name:
        with st.spinner("Lecture du fichier..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                res = requests.post(f"{API_URL}/conversation/upload", files=files, timeout=30)
                if res.status_code == 200:
                    st.session_state['conversation_data'] = res.json()
                    st.session_state['current_filename'] = uploaded_file.name
                    st.session_state['analysis_done'] = False
                    st.session_state['agent_result'] = None
                else:
                    st.error(f"Erreur Upload: {res.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Impossible de se connecter a l'API: {API_URL}")
            except Exception as e:
                st.error(f"Erreur: {e}")

# Interface principale
if st.session_state['conversation_data'] is not None:
    json_payload = st.session_state['conversation_data']

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
            with st.spinner("Analyse clinique..."):
                try:
                    response = requests.post(f"{API_URL}/conversation/agent-audit", json=json_payload, timeout=120)
                    if response.status_code == 200:
                        res = response.json()
                        st.session_state['agent_result'] = res
                        st.session_state['last_agent_audit'] = res
                        st.session_state['analysis_done'] = True
                        st.rerun()
                    else:
                        st.error(f"Erreur API: {response.text}")
                except requests.exceptions.Timeout:
                    st.error("Timeout - Reessayez")
                except Exception as e:
                    st.error(f"Erreur: {e}")

    if st.session_state['analysis_done'] and st.session_state['agent_result']:
        res = st.session_state['agent_result']
        extracted = res.get("extracted_data", {})
        constantes = extracted.get('constantes', {}) if extracted else {}
        alert = res.get("protocol_alert")
        missing_info = res.get("missing_info", [])

        st.divider()
        col_data, col_decision = st.columns([1, 1])

        with col_data:
            st.subheader("Donnees Structurees")
            m1, m2, m3 = st.columns(3)
            with m1:
                douleur = constantes.get('echelle_douleur')
                st.metric("Douleur", f"{douleur}/10" if douleur is not None else "-")
            with m2:
                temp = constantes.get('temperature')
                st.metric("Temperature", f"{temp}C" if temp else "-")
            with m3:
                age = extracted.get('age')
                st.metric("Age", f"{age} ans" if age else "-")

            with st.expander("Dossier complet", expanded=True):
                st.json(extracted)

        with col_decision:
            st.subheader("Copilote IA")
            if alert:
                st.error(f"**ALERTE PROTOCOLE**\n\n{alert}")
            else:
                st.success("Aucun indicateur de gravite immediate.")

            if missing_info:
                st.warning("**Informations a demander:**")
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
        if st.button("Nouvelle Analyse"):
            st.session_state['analysis_done'] = False
            st.rerun()

else:
    st.info("Veuillez charger un fichier pour commencer.")
