import streamlit as st
import sys
from pathlib import Path

current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

st.title("Dashboard & Monitoring")
st.caption("Pilotage de la requete LLM")

if 'last_simulation' in st.session_state and st.session_state['last_simulation']:
    sim = st.session_state['last_simulation']
    metrics = sim['metrics']

    st.subheader("Performance & Impact")
    k1, k2, k3, k4 = st.columns(4)

    k1.metric(label="Cout Est.", value=f"${metrics['cost_usd']:.5f}")
    k2.metric(label="Latence", value=f"{metrics['latency_ms']:.0f} ms", delta=f"{metrics['total_tokens']} tokens")

    co2_val = metrics.get('gwp_kgco2')
    k3.metric(label="Empreinte CO2", value=f"{co2_val*1000:.4f}", delta="g (CO2eq)", delta_color="off")

    nrj_val = metrics.get('energy_kwh')
    k4.metric(label="Energie", value=f"{nrj_val*1000:.4f}", delta="Wh", delta_color="off")

    st.divider()
    st.subheader("Details Modele")
    st.code(f"""
    Provider : {metrics['provider']}
    Modele   : {metrics['model_name']}
    Tokens   : {metrics['input_tokens']} (Prompt) + {metrics['output_tokens']} (Completion)
    Total    : {metrics['total_tokens']} tokens
    """)

else:
    st.info("Aucune analyse recente en memoire.")
    st.markdown("""
    Pour generer des metriques:
    1. Allez dans **Accueil**
    2. Chargez une conversation
    3. Cliquez sur **Lancer le Copilote**
    """)
