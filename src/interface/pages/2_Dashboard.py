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

st.title("Dashboard & Monitoring")
st.caption("Pilotage de la requête LLM")

if 'last_simulation' in st.session_state and st.session_state['last_simulation']:
    sim = st.session_state['last_simulation']
    metrics = sim['metrics']

    # =============================================
    # ENCADRÉ 1 : MÉTRIQUES DE LA DERNIÈRE REQUÊTE
    # =============================================
    with st.container(border=True):
        st.subheader("📍 Dernière requête")

        # --- 1. KPI PRINCIPAUX ---
        st.markdown("**Performance & Impact**")

        k1, k2, k3, k4 = st.columns(4)

        # Coût - Grille tarifaire par modèle ($/M tokens)
        prix_modeles = {
            "mistral/mistral-small-latest": {"input": 0.1, "output": 0.3},
            "mistral/mistral-medium-latest": {"input": 0.4, "output": 2.0},
            "mistral/mistral-large-latest": {"input": 0.5, "output": 1.5},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        }
        model_name = metrics.get('model_name', 'inconnu')
        prix = prix_modeles.get(model_name, None)
        if prix:
            help_prix = f"Modèle : {model_name}\nTarif : {prix['input']} USD/M tokens (input) / {prix['output']} USD/M tokens (output)"
        else:
            help_prix = f"Modèle : {model_name}\nTarif : non référencé"

        k1.metric(
            label="Coût Est.",
            value=f"${metrics['cost_usd']:.5f}",
            help=help_prix
        )

        # Latence
        k2.metric(
            label="Latence",
            value=f"{metrics['latency_ms']:.0f} ms",
            delta=f"{metrics['total_tokens']} tokens"
        )

        # Impact Carbone
        co2_val = metrics.get('gwp_kgco2') or 0
        co2_g = co2_val * 1000  # Conversion kg -> g
        # Analogies : 1 recherche Google ≈ 0.2g CO2, 1 email ≈ 0.3g CO2
        nb_google = co2_g / 0.2
        nb_emails = co2_g / 0.3
        k3.metric(
            label="Empreinte CO2",
            value=f"{co2_g:.4f}",
            delta="g (CO2eq)",
            delta_color="off",
            help=f"≈ {nb_google:.2f} recherche(s) Google\n≈ {nb_emails:.2f} email(s) envoyé(s)"
        )

        # Energie
        nrj_val = metrics.get('energy_kwh') or 0
        nrj_wh = nrj_val * 1000  # Conversion kWh -> Wh
        # Analogie : 1 Wh = 60 sec d'ampoule 60W (60W * 1min = 1Wh)
        sec_ampoule_nrj = nrj_wh * 60
        k4.metric(
            label="Énergie",
            value=f"{nrj_wh:.4f}",
            delta="Wh",
            delta_color="off",
            help=f"≈ {sec_ampoule_nrj:.1f} sec d'ampoule 60W"
        )

        st.divider()

        # --- 2. MÉTRIQUES MÉTIER ---
        st.markdown("**Métriques Métier**")

        triage = sim.get('triage_result', {})

        m1, m2 = st.columns(2)

        # Score de confiance
        confidence = triage.get('confidence_score', 0)
        confidence_pct = confidence * 100
        if confidence >= 0.8:
            confidence_color = "normal"
        else:
            confidence_color = "off"
        m1.metric(
            label="Confiance",
            value=f"{confidence_pct:.0f}%",
            delta="Élevée" if confidence >= 0.8 else "À vérifier",
            delta_color=confidence_color,
            help="Score de confiance du modèle.\n≥ 80% : Fiable\n< 80% : Vérification humaine recommandée"
        )

        # Nombre de Red Flags
        red_flags = triage.get('red_flags', [])
        nb_flags = len(red_flags)
        flags_tooltip = "Signaux d'alerte :\n" + "\n".join([f"• {f}" for f in red_flags]) if red_flags else "Aucun signal d'alerte"
        m2.metric(
            label="Red Flags",
            value=nb_flags,
            delta="Alerte" if nb_flags > 0 else "RAS",
            delta_color="inverse" if nb_flags > 0 else "off",
            help=flags_tooltip
        )

        st.divider()

        # --- 3. DETAILS TECHNIQUES ---
        st.markdown("**Détails Modèle**")

        st.code(f"""
    Provider : {metrics['provider']}
    Modèle   : {metrics['model_name']}
    Tokens   : {metrics['input_tokens']} (Prompt) + {metrics['output_tokens']} (Completion)
    Total    : {metrics['total_tokens']} tokens
        """)

    # =============================================
    # ENCADRÉ 2 : MÉTRIQUES GLOBALES (SESSION)
    # =============================================
    with st.container(border=True):
        st.subheader("📊 Toutes les requêtes (session)")

        history = st.session_state.get('triage_history', [])
        metrics_history = st.session_state.get('metrics_history', [])

        # Consommation totale de la session
        if metrics_history:
            total_cost = sum(m.get('cost_usd', 0) or 0 for m in metrics_history)
            total_co2 = sum((m.get('gwp_kgco2', 0) or 0) * 1000 for m in metrics_history)  # en g
            total_energy = sum((m.get('energy_kwh', 0) or 0) * 1000 for m in metrics_history)  # en Wh

            # Analogies pour les totaux
            total_google = total_co2 / 0.2
            total_emails = total_co2 / 0.3
            total_sec_ampoule = total_energy * 60

            st.markdown("**Consommation totale**")
            t1, t2, t3 = st.columns(3)
            t1.metric(
                label="Coût total",
                value=f"${total_cost:.5f}",
                help=f"Cumul des {len(metrics_history)} requête(s)"
            )
            t2.metric(
                label="CO2 total",
                value=f"{total_co2:.4f} g",
                help=f"≈ {total_google:.2f} recherche(s) Google\n≈ {total_emails:.2f} email(s) envoyé(s)"
            )
            t3.metric(
                label="Énergie totale",
                value=f"{total_energy:.4f} Wh",
                help=f"≈ {total_sec_ampoule:.1f} sec d'ampoule 60W"
            )

            st.divider()
        if history:
            total = len(history)
            counts = {
                "ROUGE": history.count("ROUGE"),
                "JAUNE": history.count("JAUNE"),
                "VERT": history.count("VERT"),
                "GRIS": history.count("GRIS")
            }

            r1, r2, r3, r4 = st.columns(4)
            r1.metric(
                label="🔴 ROUGE",
                value=counts["ROUGE"],
                delta=f"{(counts['ROUGE']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r2.metric(
                label="🟡 JAUNE",
                value=counts["JAUNE"],
                delta=f"{(counts['JAUNE']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r3.metric(
                label="🟢 VERT",
                value=counts["VERT"],
                delta=f"{(counts['VERT']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )
            r4.metric(
                label="⚪ GRIS",
                value=counts["GRIS"],
                delta=f"{(counts['GRIS']/total*100):.0f}%" if total > 0 else "0%",
                delta_color="off"
            )

            st.caption(f"Total : {total} patient(s) analysé(s) cette session")
        else:
            st.info("Aucun historique pour cette session.")

else:
    st.info("Aucune analyse récente en mémoire.")
    st.markdown("""
    Pour générer des métriques :
    1. Allez dans l'onglet **Accueil**.
    2. Chargez une conversation.
    3. Cliquez sur **"Extraire les infos"**.
    """)