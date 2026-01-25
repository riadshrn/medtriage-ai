import streamlit as st
import sys
sys.path.append("..")
from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

# Page Dashboard
st.title("Dashboard")

st.markdown("*Ici seront affichées les métriques*")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Métrique 1", value="--")
with col2:
    st.metric(label="Métrique 2", value="--")
with col3:
    st.metric(label="Métrique 3", value="--")

with st.container(border=True, height=300):
    st.markdown("*Zone réservée pour les métriques*")
