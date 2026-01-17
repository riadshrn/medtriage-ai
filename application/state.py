import streamlit as st

def init_session_state():
    """Initialise les session states globaux."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "categorie" not in st.session_state:
        st.session_state.categorie = ""

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
