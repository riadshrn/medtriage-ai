import streamlit as st
import sys
sys.path.append("..")
from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

# Page Accueil
st.title("Accueil")

col_left, col_right = st.columns(2)

with col_left:
    with st.container(border=True, height=250):
        st.markdown("*Liste des paramètres résumés (type JSON) apparaît ici*")

with col_right:
    with st.container(border=True, height=250):
        st.markdown("*Des questions seront proposées à l'infirmier(e)*")

st.markdown("**Catégorie prédite**")
col_cat, col_btn = st.columns([4, 1])
with col_cat:
    if st.session_state.edit_mode:
        new_categorie = st.text_input(
            "Catégorie",
            value=st.session_state.categorie,
            label_visibility="collapsed",
            placeholder="Catégorie prédite...",
            key="cat_input"
        )
    else:
        st.text_input(
            "Catégorie",
            value=st.session_state.categorie,
            label_visibility="collapsed",
            placeholder="Catégorie prédite...",
            disabled=True,
            key="cat_display"
        )
with col_btn:
    if st.session_state.edit_mode:
        if st.button("Valider", use_container_width=True):
            st.session_state.categorie = new_categorie
            st.session_state.edit_mode = False
            st.rerun()
    else:
        if st.button("Edit", use_container_width=True):
            st.session_state.edit_mode = True
            st.rerun()
