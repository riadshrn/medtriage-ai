import streamlit as st

def init_session_state():
    """Initialise les session states globaux."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "categorie" not in st.session_state:
        st.session_state.categorie = ""
        
    if "triage_color" not in st.session_state:
        st.session_state.triage_color = None 

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if "triage_history" not in st.session_state:
        st.session_state.triage_history = []

    if "metrics_history" not in st.session_state:
        st.session_state.metrics_history = []

    # Dernière requête (toutes sources confondues)
    if "last_request_metrics" not in st.session_state:
        st.session_state.last_request_metrics = None

    if "last_request_source" not in st.session_state:
        st.session_state.last_request_source = None

    # Historique Mode Interactif
    if "interactive_metrics_history" not in st.session_state:
        st.session_state.interactive_metrics_history = []
