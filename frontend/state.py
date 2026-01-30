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

    # Historique Mode Interactif (par triage complété)
    if "interactive_metrics_history" not in st.session_state:
        st.session_state.interactive_metrics_history = []

    # Historique des niveaux de triage Mode Interactif (ROUGE, JAUNE, VERT, GRIS)
    if "interactive_triage_history" not in st.session_state:
        st.session_state.interactive_triage_history = []

    # Métriques de la session interactive en cours (accumulées jusqu'au triage)
    if "current_interactive_session_metrics" not in st.session_state:
        st.session_state.current_interactive_session_metrics = {
            'cost_usd': 0,
            'gwp_kgco2': 0,
            'energy_kwh': 0,
            'nb_calls': 0
        }
