import streamlit as st
import os
import sys
from pathlib import Path

# Config habituelle
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))
from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

st.title("📊 Dashboard & Monitoring")
st.caption("Pilotage de la requête LLM")

if 'last_simulation' in st.session_state and st.session_state['last_simulation']:
    sim = st.session_state['last_simulation']
    metrics = sim['metrics']
    
    # --- 1. KPI PRINCIPAUX ---
    st.subheader("Performance & Impact (Requête Unique)")
    
    k1, k2, k3, k4 = st.columns(4)
    
    # Coût
    k1.metric(
        label="Coût Est.",
        value=f"${metrics['cost_usd']:.5f}",
        help="Basé sur la grille tarifaire fournie"
    )
    
    # Latence
    k2.metric(
        label="Latence",
        value=f"{metrics['latency_ms']:.0f} ms",
        delta=f"{metrics['total_tokens']} tokens"
    )
    
    # Impact Carbone
    co2_val = metrics.get('gwp_kgco2')
    k3.metric(
        label="Empreinte CO2",
        value=f"{co2_val*1000:.4f}",  # Juste le chiffre
        delta="g (CO2eq)",            # L'unité en dessous
        delta_color="off",            # "off" pour gris (neutre), "inverse" pour rouge si élevé
        help="Global Warming Potential"
    )
    
    # Energie
    nrj_val = metrics.get('energy_kwh')
    k4.metric(
        label="Énergie",
        value=f"{nrj_val*1000:.4f}",  # Juste le chiffre
        delta="Wh",                   # L'unité en dessous
        delta_color="off"
    )

    st.divider()

    # --- 2. DETAILS TECHNIQUES ---
    # Plus de colonnes ML ici, juste les détails du modèle
    st.subheader("Détails Modèle")
    
    # Création d'un dataframe ou d'un affichage json propre pour les détails
    st.code(f"""
    Provider : {metrics['provider']}
    Modèle   : {metrics['model_name']}
    Tokens   : {metrics['input_tokens']} (Prompt) + {metrics['output_tokens']} (Completion)
    Total    : {metrics['total_tokens']} tokens
    """)

else:
    st.info("Aucune analyse récente en mémoire.")
    st.markdown("""
    Pour générer des métriques :
    1. Allez dans l'onglet **Accueil**.
    2. Chargez une conversation.
    3. Cliquez sur **"Extraire les infos"**.
    """)