import streamlit as st

st.set_page_config(
    page_title="MedTriage-AI",
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

# Page d'accueil par defaut (sans switch_page pour compatibilite HF Spaces)
st.title("🏥 MedTriage-AI")
st.markdown("""
### Bienvenue sur MedTriage-AI

Utilisez le menu lateral pour naviguer entre les pages :

- **Accueil** : Triage par description textuelle
- **Mode interactif** : Simulation avec constantes vitales
- **Dashboard** : Metriques GreenOps/FinOps
- **Feedback** : Historique et retours infirmiers
- **MLFlow** : Suivi des modeles ML
""")

st.info("Selectionnez une page dans le menu a gauche pour commencer.")
