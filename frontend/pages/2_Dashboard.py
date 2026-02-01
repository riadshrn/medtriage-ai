"""
Dashboard - Pilotage GreenOps / FinOps.

Cette page affiche les métriques d'impact environnemental et de coût
des requêtes LLM effectuées dans l'application.

Les données proviennent de l'historique persistant (history.json via API).
"""

import os
import streamlit as st
import requests
import sys
from pathlib import Path

current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from style import  configure_page, apply_style
from state import init_session_state

# IMPORTANT: configure_page DOIT être appelée EN PREMIER
configure_page(page_title="Dashboard - MedTriage-AI")
init_session_state()
apply_style()

# URL de l'API Backend
API_URL = os.getenv("API_URL", "http://backend:8000")

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


def get_history_stats():
    """Récupère les statistiques depuis l'API /history/stats."""
    try:
        response = requests.get(f"{API_URL}/history/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


# =============================================
# ENCADRE 1 : METRIQUES DERNIERE REQUETE
# =============================================
metrics = st.session_state.get('last_request_metrics')
source = st.session_state.get('last_request_source')

if metrics:
    with st.container(border=True):
        st.subheader("Informations du dernier triage")
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
        st.subheader("Informations du dernier triage")
        st.info("Aucun triage effectué. Lancez une analyse depuis l'Accueil ou le Mode Interactif.")

# =============================================
# ENCADRE 2 : METRIQUES GLOBALES (HISTORIQUE PERSISTANT)
# =============================================
with st.container(border=True):
    st.subheader("Statistiques globales (historique persistant)")

    # Récupérer les stats depuis l'API
    stats = get_history_stats()

    if stats is None:
        st.warning("Impossible de récupérer les statistiques. Vérifiez la connexion à l'API.")
    elif stats.get('total_triages', 0) == 0:
        st.info("Aucun triage enregistré dans l'historique.")
    else:
        total_triages = stats.get('total_triages', 0)
        by_gravity = stats.get('by_gravity', {})
        by_source = stats.get('by_source', {})
        metrics_stats = stats.get('metrics_stats', {})

        # --- METRIQUES GREENOPS/FINOPS CUMULEES ---
        if metrics_stats and metrics_stats.get('requests_with_metrics', 0) > 0:
            total_cost = metrics_stats.get('total_cost_usd', 0)
            total_co2 = metrics_stats.get('total_gwp_kgco2', 0) * 1000  # en g
            total_energy = metrics_stats.get('total_energy_kwh', 0) * 1000  # en Wh
            total_tokens_all = metrics_stats.get('total_tokens', 0)
            avg_latency = metrics_stats.get('avg_latency_s', 0) * 1000  # en ms
            requests_with_metrics = metrics_stats.get('requests_with_metrics', 0)

            # Analogies pour les totaux
            total_google = total_co2 / 0.2 if total_co2 > 0 else 0
            total_min_ampoule = total_energy

            st.markdown("**Consommation totale (tous triages)**")
            st.caption(f"{requests_with_metrics} triage(s) avec métriques sur {total_triages} total")

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

            # Ligne supplémentaire pour tokens et latence moyenne
            t4, t5, t6 = st.columns(3)
            t4.metric(
                label="Tokens totaux",
                value=f"{total_tokens_all:,}"
            )
            t5.metric(
                label="Latence moyenne",
                value=f"{avg_latency:.0f} ms"
            )
            t6.metric(
                label="Triages avec métriques",
                value=f"{requests_with_metrics}/{total_triages}"
            )

            st.divider()

        # --- REPARTITION PAR NIVEAU DE TRIAGE ---
        colors = {
            "ROUGE": "#DC2626",
            "JAUNE": "#F59E0B",
            "VERT": "#10B981",
            "GRIS": "#6B7280"
        }

        st.markdown("**Répartition des niveaux de triage**")

        r1, r2, r3, r4 = st.columns(4)

        for col, level in zip([r1, r2, r3, r4], ["ROUGE", "JAUNE", "VERT", "GRIS"]):
            count = by_gravity.get(level, 0)
            pct = (count / total_triages * 100) if total_triages > 0 else 0
            with col:
                st.markdown(
                    f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{colors[level]};margin-right:6px;vertical-align:middle;"></span>**{level}**',
                    unsafe_allow_html=True
                )
                st.metric(
                    label="",
                    value=count,
                    delta=f"{pct:.0f}%",
                    delta_color="off",
                    label_visibility="collapsed"
                )

        # --- REPARTITION PAR SOURCE ---
        st.divider()
        st.markdown("**Répartition par source**")

        nb_accueil = by_source.get('accueil', 0)
        nb_simulation = by_source.get('simulation', 0)
        nb_api = by_source.get('api', 0)

        s1, s2, s3 = st.columns(3)
        s1.metric(label="Accueil", value=nb_accueil)
        s2.metric(label="Simulation", value=nb_simulation)
        s3.metric(label="API", value=nb_api)

        st.caption(f"Total : {total_triages} patient(s) trié(s)")

        # --- DERNIERE DATE DE TRIAGE ---
        last_date = stats.get('last_triage_date')
        if last_date:
            st.caption(f"Dernier triage : {last_date[:19].replace('T', ' ')}")
