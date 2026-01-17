import streamlit as st
import sys
sys.path.append("..")
from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

# Page Test
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
    user_input = st.text_input(
        "Message",
        label_visibility="collapsed",
        placeholder="Script...",
        key="chat_input"
    )

with col_send:
    if st.button("➤", use_container_width=True):
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            # TODO: Remplacer par l'appel à votre algorithme
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Réponse placeholder..."
            })
            st.rerun()
