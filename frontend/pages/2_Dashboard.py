"""
Dashboard - Pilotage GreenOps / FinOps.

Cette page affiche les métriques d'impact environnemental et de coût
des requêtes LLM effectuées dans l'application.
"""

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
st.caption("Pilotage GreenOps / FinOps")

# Prix des modeles (USD par million de tokens)
prix_modeles = {
    "mistral/mistral-small-latest": {"input": 0.1, "output": 0.3},
    "mistral/mistral-medium-latest": {"input": 0.4, "output": 2.0},
    "mistral/mistral-large-latest": {"input": 0.5, "output": 1.5},
    "mistral-small-latest": {"input": 0.1, "output": 0.3},
    "mistral-medium-latest": {"input": 0.4, "output": 2.0},
    "mistral-large-latest": {"input": 0.5, "output": 1.5},
}

# =============================================
# ENCADRE 1 : METRIQUES DERNIERE REQUETE
# =============================================
metrics = st.session_state.get('last_request_metrics')
source = st.session_state.get('last_request_source')

if metrics:
    with st.container(border=True):
        st.subheader("Dernière requête")
        st.info(f"Source: **{source}**")

        # --- 1. METRIQUES GREENOPS/FINOPS ---
        st.markdown("**Impact Environnemental & Coût**")
        k1, k2, k3, k4 = st.columns(4)

        # Cout avec tooltip prix
        cost_val = metrics.get('cost_usd', 0) or 0
        model_name = metrics.get('model_name', 'inconnu')
        prix_info = prix_modeles.get(model_name, None)
        if prix_info:
            help_prix = f"Tarif {model_name}:\n- Input: ${prix_info['input']}/M tokens\n- Output: ${prix_info['output']}/M tokens"
        else:
            help_prix = f"Tarif {model_name}: non référencé"
        k1.metric(
            label="Coût Est.",
            value=f"${cost_val:.5f}",
            help=help_prix
        )

        # Latence
        latency_val = metrics.get('latency_s', 0) or 0
        latency_ms = latency_val * 1000
        total_tokens = metrics.get('total_tokens', 0)
        k2.metric(
            label="Latence",
            value=f"{latency_ms:.0f}",
            delta=f"ms ({total_tokens} tokens)",
            delta_color="off"
        )

        # CO2 avec analogie recherche Google uniquement
        co2_val = metrics.get('gwp_kgco2', 0) or 0
        co2_g = co2_val * 1000  # Conversion kg -> g
        # Analogie : 1 recherche Google = 0.2g CO2
        nb_google = co2_g / 0.2 if co2_g > 0 else 0
        k3.metric(
            label="Empreinte CO2",
            value=f"{co2_g:.4f}",
            delta="g (CO2eq)",
            delta_color="off",
            help=f"Environ {nb_google:.2f} recherche(s) Google"
        )

        # Energie avec analogie ampoule en minutes
        nrj_val = metrics.get('energy_kwh', 0) or 0
        nrj_wh = nrj_val * 1000  # Conversion kWh -> Wh
        # Analogie : 1 Wh = 1 min d'ampoule 60W (60W pendant 1h = 60Wh, donc 1Wh = 1min)
        min_ampoule = nrj_wh
        k4.metric(
            label="Énergie",
            value=f"{nrj_wh:.4f}",
            delta="Wh",
            delta_color="off",
            help=f"Environ {min_ampoule:.2f} min d'ampoule 60W"
        )

        st.divider()

        # --- 2. DETAILS MODELE ---
        st.markdown("**Détails Modèle**")
        provider = metrics.get('provider', 'N/A')
        input_tokens = metrics.get('input_tokens', 0)
        output_tokens = metrics.get('output_tokens', 0)

        st.code(f"""
Provider : {provider}
Modèle   : {model_name}
Tokens   : {input_tokens} (Prompt) + {output_tokens} (Completion)
Total    : {total_tokens} tokens
        """)
else:
    with st.container(border=True):
        st.subheader("Dernière requête")
        st.info("Aucune requête effectuée. Lancez une analyse depuis l'Accueil ou le Mode Interactif.")

# =============================================
# ENCADRE 2 : METRIQUES GLOBALES (SESSION)
# =============================================
with st.container(border=True):
    st.subheader("Toutes les requêtes (session)")

    # Historiques des deux sources
    history = st.session_state.get('triage_history', [])
    metrics_history = st.session_state.get('metrics_history', [])
    interactive_history = st.session_state.get('interactive_metrics_history', [])

    # Combiner les deux historiques de métriques
    all_metrics = metrics_history + interactive_history
    nb_accueil = len(metrics_history)
    nb_interactif = len(interactive_history)

    if not history and not all_metrics:
        st.info("Aucune analyse effectuée dans cette session.")
    else:
        # Consommation totale de la session (toutes sources)
        if all_metrics:
            total_cost = sum(m.get('cost_usd', 0) or 0 for m in all_metrics)
            total_co2 = sum((m.get('gwp_kgco2', 0) or 0) * 1000 for m in all_metrics)  # en g
            total_energy = sum((m.get('energy_kwh', 0) or 0) * 1000 for m in all_metrics)  # en Wh

            # Analogies pour les totaux
            total_google = total_co2 / 0.2 if total_co2 > 0 else 0
            total_min_ampoule = total_energy

            st.markdown("**Consommation totale**")
            st.caption(f"Accueil: {nb_accueil} requête(s) | Mode Interactif: {nb_interactif} requête(s)")

            t1, t2, t3 = st.columns(3)
            t1.metric(
                label="Coût total",
                value=f"${total_cost:.5f}"
            )
            t2.metric(
                label="CO2 total",
                value=f"{total_co2:.4f} g",
                help=f"Environ {total_google:.2f} recherche(s) Google"
            )
            t3.metric(
                label="Énergie totale",
                value=f"{total_energy:.4f} Wh",
                help=f"Environ {total_min_ampoule:.2f} min d'ampoule 60W"
            )

            st.divider()

        # Répartition des niveaux de triage (seulement pour Accueil)
        if history:
            st.markdown("**Répartition des niveaux de triage**")
            total = len(history)
            counts = {
                "ROUGE": history.count("ROUGE"),
                "JAUNE": history.count("JAUNE"),
                "VERT": history.count("VERT"),
                "GRIS": history.count("GRIS")
            }

            r1, r2, r3, r4 = st.columns(4)
            r1.metric(
                label="ROUGE",
                value=counts["ROUGE"],
                delta=f"{(counts['ROUGE']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r2.metric(
                label="JAUNE",
                value=counts["JAUNE"],
                delta=f"{(counts['JAUNE']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r3.metric(
                label="VERT",
                value=counts["VERT"],
                delta=f"{(counts['VERT']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r4.metric(
                label="GRIS",
                value=counts["GRIS"],
                delta=f"{(counts['GRIS']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )

            st.caption(f"Total : {total} patient(s) trié(s) dans cette session")
