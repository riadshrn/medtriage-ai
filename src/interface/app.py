import streamlit as st

st.set_page_config(
    page_title="Triage urgences",
    page_icon="🏥",
    layout="wide"
)

# Initialisation des session states globaux
if "messages" not in st.session_state:
    st.session_state.messages = []

if "categorie" not in st.session_state:
    st.session_state.categorie = ""

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Redirige automatiquement vers la page Accueil
st.switch_page("pages/0_Accueil.py")
