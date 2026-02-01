import streamlit as st

st.set_page_config(
    page_title="MedTriage-AI",
    page_icon="🏥",
    layout="wide"
)

# Initialisation des session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "categorie" not in st.session_state:
    st.session_state.categorie = ""
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Page d'accueil
st.title("🏥 MedTriage-AI")
st.markdown("""
### Systeme intelligent de triage medical

Utilisez le **menu lateral** (a gauche) pour naviguer entre les pages :

| Page | Description |
|------|-------------|
| **Accueil** | Triage par description textuelle |
| **Mode Interactif** | Simulation avec constantes vitales |
| **Dashboard** | Metriques GreenOps/FinOps |
| **Feedback** | Historique et retours infirmiers |
| **MLFlow** | Suivi des modeles ML |
""")

st.success("Application deployee avec succes sur Hugging Face Spaces!")
