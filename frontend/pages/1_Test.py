import streamlit as st
import sys
from pathlib import Path

current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

st.title("Test")

with st.container(border=True, height=350):
    if st.session_state.messages:
        for msg in st.session_state.messages:
            icon = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(f"{icon} {msg['content']}")
    else:
        st.markdown("*Champ qui affiche une discussion*")

col_input, col_send = st.columns([6, 1])

with col_input:
    user_input = st.text_input("Message", label_visibility="collapsed", placeholder="Script...", key="chat_input")

with col_send:
    if st.button("Envoyer", use_container_width=True):
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": "Reponse placeholder..."})
            st.rerun()
