"""
Benchmark Éco-Performance - Comparaison des modèles Mistral.

Compare les modèles Mistral sur les 3 usages principaux afin de trouver
le modèle le plus sobre énergétiquement tout en restant performant.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuration des chemins pour importer depuis le parent
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from state import init_session_state
from style import configure_page, apply_style

# Initialisation
configure_page(page_title="Benchmark - MedTriage-AI", page_icon="🌱")
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://backend:8000")

# Configuration des modèles (4 tailles) - Prix officiels Mistral AI 2025
# Source : https://mistral.ai/pricing
MODELES_MISTRAL = {
    "ministral-3b-latest": {
        "display_name": "Ministral 3B",
        "input_price": 0.04,
        "output_price": 0.04,
        "description": "Ultra-léger",
        "icon": "🪶"
    },
    "mistral-small-latest": {
        "display_name": "Mistral Small",
        "input_price": 0.1,
        "output_price": 0.3,
        "description": "Rapide",
        "icon": "🚀"
    },
    "mistral-medium-latest": {
        "display_name": "Mistral Medium",
        "input_price": 0.4,
        "output_price": 2.0,
        "description": "Équilibré",
        "icon": "⚖️"
    },
    "mistral-large-latest": {
        "display_name": "Mistral Large",
        "input_price": 2.0,
        "output_price": 6.0,
        "description": "Précision",
        "icon": "🎯"
    }
}

# Cas de simulation prédéfinis avec plusieurs questions
SIMULATION_CASES = {
    "douleur_thoracique": {
        "name": "Douleur Thoracique",
        "persona": """Tu es un patient de 58 ans, homme, fumeur (30 ans, 1 paquet/jour).
SYMPTÔMES : Douleur thoracique intense irradiant vers le bras gauche depuis 1h. Tu transpires et as des nausées.
ANTÉCÉDENTS : Hypertension, cholestérol. Père décédé d'infarctus à 55 ans.
CONSTANTES : FC=110, PA=155/95, T=37.2, SpO2=94%, Douleur=8/10
COMPORTEMENT : Tu es très anxieux, tu as peur de mourir.""",
        "questions": [
            "Pouvez-vous me décrire votre douleur ?",
            "Depuis quand avez-vous mal ?",
            "Avez-vous des antécédents cardiaques ?",
            "Prenez-vous des médicaments ?"
        ]
    },
    "detresse_respiratoire": {
        "name": "Détresse Respiratoire",
        "persona": """Tu es une patiente de 45 ans, asthmatique connue.
SYMPTÔMES : Crise sévère depuis 30min, tu parles difficilement par phrases courtes.
ANTÉCÉDENTS : Asthme sévère, nombreuses hospitalisations. Tu n'as pas pris ton traitement depuis 2 jours.
CONSTANTES : FC=120, PA=140/90, T=37.0, SpO2=88%, FR=28, Douleur=6/10
COMPORTEMENT : Tu es paniquée, tu n'arrives pas à reprendre ton souffle.""",
        "questions": [
            "Depuis quand avez-vous du mal à respirer ?",
            "Avez-vous pris votre traitement ?",
            "Est-ce que vous pouvez me dire une phrase complète ?",
            "Avez-vous déjà eu des crises comme ça ?"
        ]
    },
    "douleur_abdominale": {
        "name": "Douleur Abdominale",
        "persona": """Tu es une patiente de 35 ans.
SYMPTÔMES : Douleur abdominale intense en fosse iliaque droite depuis 12h. Fièvre et nausées depuis ce matin.
ANTÉCÉDENTS : Aucun antécédent notable.
CONSTANTES : FC=95, PA=125/80, T=38.5, SpO2=98%, Douleur=7/10
COMPORTEMENT : Tu as mal quand on appuie sur le ventre à droite et tu n'as pas pu manger.""",
        "questions": [
            "Où avez-vous mal exactement ?",
            "Depuis quand avez-vous cette douleur ?",
            "Avez-vous de la fièvre ?",
            "Avez-vous pu manger ?"
        ]
    },
    "traumatisme_cranien": {
        "name": "Traumatisme Crânien",
        "persona": """Tu es un patient de 25 ans, chute de vélo il y a 30min.
SYMPTÔMES : Mal à la tête, un peu confus, bosse sur le front. Tu ne te souviens pas bien de l'accident.
ANTÉCÉDENTS : Aucun.
CONSTANTES : FC=85, PA=130/85, T=36.8, SpO2=99%, Glasgow=14, Douleur=5/10
COMPORTEMENT : Tu as des nausées et la lumière te gêne.""",
        "questions": [
            "Vous souvenez-vous de ce qui s'est passé ?",
            "Avez-vous perdu connaissance ?",
            "Avez-vous des nausées ou des vomissements ?",
            "Est-ce que la lumière vous gêne ?"
        ]
    }
}

# Labels énergétiques
ENERGY_LABELS = {
    "A": {"color": "#22C55E", "description": "Excellent"},
    "B": {"color": "#84CC16", "description": "Très bien"},
    "C": {"color": "#EAB308", "description": "Correct"},
    "D": {"color": "#F97316", "description": "Élevé"},
    "E": {"color": "#EF4444", "description": "Très élevé"}
}

# Couleurs des niveaux de triage
TRIAGE_COLORS = {
    "ROUGE": "#DC2626",
    "JAUNE": "#F59E0B",
    "VERT": "#10B981",
    "GRIS": "#6B7280"
}

# Ordre d'affichage des modèles (du plus petit au plus grand)
MODEL_ORDER = [
    "ministral-3b-latest",
    "mistral-small-latest",
    "mistral-medium-latest",
    "mistral-large-latest"
]


def sort_results_by_model_size(results: Dict) -> Dict:
    """Trie les résultats par taille de modèle (Mini > Small > Medium > Large)."""
    sorted_results = {}
    for model_key in MODEL_ORDER:
        if model_key in results:
            sorted_results[model_key] = results[model_key]
    return sorted_results


def init_benchmark_state():
    """Initialise l'état de la session."""
    defaults = {
        "benchmark_results": {},
        "selected_models_extraction": ["ministral-3b-latest", "mistral-small-latest"],
        "selected_models_agent": ["ministral-3b-latest", "mistral-small-latest"],
        "selected_models_simulation": ["ministral-3b-latest", "mistral-small-latest"],
        "conversations_cache": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_benchmark_state():
    """Remet à zéro l'état du benchmark."""
    st.session_state.benchmark_results = {}
    st.session_state.selected_models_extraction = ["ministral-3b-latest", "mistral-small-latest"]
    st.session_state.selected_models_agent = ["ministral-3b-latest", "mistral-small-latest"]
    st.session_state.selected_models_simulation = ["ministral-3b-latest", "mistral-small-latest"]


def load_conversations() -> List[Dict]:
    """Charge la liste des conversations depuis l'API."""
    if st.session_state.conversations_cache:
        return st.session_state.conversations_cache
    try:
        response = requests.get(f"{API_URL}/conversation/list", timeout=10)
        if response.status_code == 200:
            st.session_state.conversations_cache = response.json()
            return st.session_state.conversations_cache
    except requests.RequestException:
        pass
    return []


def load_conversation_content(filename: str) -> Optional[Dict]:
    """Charge le contenu d'une conversation."""
    try:
        response = requests.get(f"{API_URL}/conversation/load/{filename}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def calculate_energy_label(energy_wh: float, use_case: str) -> str:
    """Calcule le label énergétique (A-E)."""
    thresholds = {
        "extraction": {"A": 0.5, "B": 1.0, "C": 2.0, "D": 5.0},
        "agent": {"A": 1.0, "B": 2.0, "C": 5.0, "D": 10.0},
        "simulation": {"A": 0.3, "B": 0.8, "C": 1.5, "D": 3.0}
    }
    t = thresholds.get(use_case, thresholds["extraction"])

    if energy_wh <= t["A"]:
        return "A"
    elif energy_wh <= t["B"]:
        return "B"
    elif energy_wh <= t["C"]:
        return "C"
    elif energy_wh <= t["D"]:
        return "D"
    return "E"


def call_benchmark_api(endpoint: str, payload: Dict) -> Optional[Dict]:
    """Appelle l'API de benchmark."""
    try:
        response = requests.post(f"{API_URL}/benchmark/{endpoint}", json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def process_result(result: Dict, model: str, use_case: str) -> Dict:
    """Traite le résultat d'un benchmark."""
    if result and result.get("success"):
        metrics = result.get("metrics", {})
        energy_wh = (metrics.get("energy_kwh", 0) or 0) * 1000
        co2_g = (metrics.get("gwp_kgco2", 0) or 0) * 1000

        return {
            "model_key": model,
            "model_name": MODELES_MISTRAL[model]["display_name"],
            "icon": MODELES_MISTRAL[model]["icon"],
            "success": True,
            "latency_s": metrics.get("latency_s", 0) or 0,
            "cost_usd": metrics.get("cost_usd", 0) or 0,
            "co2_g": co2_g,
            "energy_wh": energy_wh,
            "energy_label": calculate_energy_label(energy_wh, use_case),
            "total_tokens": metrics.get("total_tokens", 0),
            "input_tokens": metrics.get("input_tokens", 0),
            "output_tokens": metrics.get("output_tokens", 0),
            "raw_response": result.get("response") or result.get("analysis") or result.get("extracted_data"),
            "google_equiv": co2_g / 0.2 if co2_g > 0 else 0,
            "bulb_minutes": energy_wh
        }
    return {
        "model_key": model,
        "model_name": MODELES_MISTRAL[model]["display_name"],
        "icon": MODELES_MISTRAL[model]["icon"],
        "success": False,
        "error": result.get("error", "Erreur inconnue") if result else "Pas de réponse"
    }


def render_model_selector(key: str) -> List[str]:
    """Affiche le sélecteur de modèles avec des boutons toggle."""
    st.markdown("#### Modèles à comparer")

    cols = st.columns(len(MODELES_MISTRAL))
    selected = st.session_state.get(f"selected_models_{key}", [])

    for idx, (model_key, model_info) in enumerate(MODELES_MISTRAL.items()):
        with cols[idx]:
            is_selected = model_key in selected

            if st.button(
                f"{model_info['icon']} {model_info['display_name']}",
                key=f"btn_{key}_{model_key}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                if is_selected:
                    selected.remove(model_key)
                else:
                    selected.append(model_key)
                st.session_state[f"selected_models_{key}"] = selected
                st.rerun()

            st.caption(f"{model_info['description']}")
            st.caption(f"${model_info['input_price']}/M in · ${model_info['output_price']}/M out")

    return selected


def render_comparison_chart(results: Dict):
    """Affiche le graphique comparatif avec tooltips informatifs."""
    # Tri par taille de modèle : Mini > Small > Medium > Large
    valid = sort_results_by_model_size({k: v for k, v in results.items() if v.get("success")})
    if len(valid) < 2:
        return

    models = [v["model_name"] for v in valid.values()]
    colors = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444"][:len(models)]

    # Données pour tooltips enrichis
    energy_vals = [v["energy_wh"] for v in valid.values()]
    co2_vals = [v["co2_g"] for v in valid.values()]
    cost_vals = [v["cost_usd"] for v in valid.values()]

    # Calcul des équivalences pour tooltips
    google_equivs = [v["google_equiv"] for v in valid.values()]
    bulb_mins = [v["bulb_minutes"] for v in valid.values()]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("⚡ Énergie (Wh)", "🌿 CO₂ (g)", "💰 Coût ($)")
    )

    # Énergie avec tooltip enrichi
    fig.add_trace(go.Bar(
        x=models,
        y=energy_vals,
        marker_color=colors,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>" +
                      "Énergie : %{y:.3f} Wh<br>" +
                      "≈ %{customdata:.1f} min d'ampoule 60W<br>" +
                      "<extra></extra>",
        customdata=bulb_mins
    ), row=1, col=1)

    # CO2 avec tooltip enrichi
    fig.add_trace(go.Bar(
        x=models,
        y=co2_vals,
        marker_color=colors,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>" +
                      "CO₂ : %{y:.4f} g<br>" +
                      "≈ %{customdata:.1f} recherches Google<br>" +
                      "<extra></extra>",
        customdata=google_equivs
    ), row=1, col=2)

    # Coût avec tooltip enrichi
    fig.add_trace(go.Bar(
        x=models,
        y=cost_vals,
        marker_color=colors,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>" +
                      "Coût : $%{y:.5f}<br>" +
                      "<extra></extra>"
    ), row=1, col=3)

    fig.update_layout(
        height=300,
        margin=dict(t=40, b=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="system-ui"
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def render_winner_badge(results: Dict):
    """Affiche le gagnant du benchmark."""
    valid = {k: v for k, v in results.items() if v.get("success")}
    if len(valid) < 2:
        return

    winner = min(valid.items(), key=lambda x: x[1]["energy_wh"])

    st.success(f"**{winner[1]['model_name']}** est le plus sobre avec "
               f"**{winner[1]['energy_wh']:.2f} Wh** et **{winner[1]['co2_g']:.3f} g CO₂**")


def run_extraction_benchmark(models: List[str], text: str, progress) -> Dict:
    """Exécute le benchmark d'extraction."""
    results = {}
    for idx, model in enumerate(models):
        progress.progress((idx + 1) / len(models), f"Test de {MODELES_MISTRAL[model]['display_name']}...")
        result = call_benchmark_api("extraction", {"text": text, "model": model})
        results[model] = process_result(result, model, "extraction")
    return results


def run_agent_benchmark(models: List[str], conversation: Dict, progress) -> Dict:
    """Exécute le benchmark de l'agent."""
    results = {}
    for idx, model in enumerate(models):
        progress.progress((idx + 1) / len(models), f"Test de {MODELES_MISTRAL[model]['display_name']}...")
        result = call_benchmark_api("agent", {"conversation": conversation, "model": model})
        results[model] = process_result(result, model, "agent")
    return results


def run_simulation_benchmark(models: List[str], case: Dict, nurse_message: str, progress) -> Dict:
    """Exécute le benchmark de simulation."""
    results = {}
    for idx, model in enumerate(models):
        progress.progress((idx + 1) / len(models), f"Test de {MODELES_MISTRAL[model]['display_name']}...")
        payload = {"persona": case["persona"], "history": [], "nurse_message": nurse_message, "model": model}
        result = call_benchmark_api("simulation", payload)
        results[model] = process_result(result, model, "simulation")
    return results


def render_compact_metrics(data: Dict):
    """Affiche les métriques de façon compacte dans un container."""
    label_config = ENERGY_LABELS.get(data.get("energy_label", "E"))

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
        <div style="
            width: 45px; height: 45px;
            background: {label_config['color']};
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3rem; font-weight: 800; color: white;
        ">{data.get('energy_label', '?')}</div>
        <div>
            <div style="font-weight: 600; font-size: 0.95rem;">{data['icon']} {data['model_name']}</div>
            <div style="font-size: 0.75rem; color: #666;">
                ⚡ {data['energy_wh']:.3f} Wh · 🌿 {data['co2_g']:.4f} g · 💰 ${data['cost_usd']:.5f} · ⏱️ {data['latency_s']:.1f}s
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_extraction_results(results: Dict):
    """Affiche les résultats détaillés de l'extraction côte à côte."""
    st.markdown("---")
    st.subheader("Résultats du Benchmark")

    render_winner_badge(results)
    render_comparison_chart(results)

    st.markdown("### Analyse par modèle")

    valid_results = sort_results_by_model_size({k: v for k, v in results.items() if v.get("success")})
    cols = st.columns(len(valid_results))

    for col_idx, (_, data) in enumerate(valid_results.items()):
        with cols[col_idx]:
            with st.container(border=True):
                render_compact_metrics(data)

                st.markdown("**Données extraites :**")
                raw = data.get("raw_response")
                if raw:
                    try:
                        if isinstance(raw, str):
                            parsed = json.loads(raw)
                        else:
                            parsed = raw
                        st.json(parsed)
                    except (json.JSONDecodeError, TypeError):
                        st.code(str(raw), language="json")
                else:
                    st.info("Aucune donnée")


def render_agent_results(results: Dict):
    """Affiche les résultats détaillés de l'agent côte à côte."""
    st.markdown("---")
    st.subheader("Résultats du Benchmark")

    render_winner_badge(results)
    render_comparison_chart(results)

    st.markdown("### Analyse par modèle")

    valid_results = sort_results_by_model_size({k: v for k, v in results.items() if v.get("success")})
    cols = st.columns(len(valid_results))

    for col_idx, (_, data) in enumerate(valid_results.items()):
        with cols[col_idx]:
            with st.container(border=True):
                render_compact_metrics(data)

                raw = data.get("raw_response")
                if raw:
                    try:
                        if isinstance(raw, str):
                            parsed = json.loads(raw)
                        else:
                            parsed = raw

                        # Niveau de criticité
                        criticity = parsed.get("criticity", parsed.get("gravity_level", ""))
                        if criticity:
                            color = TRIAGE_COLORS.get(criticity.upper(), "#6B7280")
                            st.markdown(f"""
                                <div style="
                                    background: {color}; color: white;
                                    padding: 10px; border-radius: 8px;
                                    text-align: center; font-weight: bold;
                                    margin: 10px 0;
                                ">TRIAGE : {criticity.upper()}</div>
                            """, unsafe_allow_html=True)

                        # Justification
                        if parsed.get("justification"):
                            st.markdown(f"**Justification :** {parsed['justification']}")

                        # Bloc uniforme pour Infos manquantes
                        missing = parsed.get("missing_info", [])
                        if missing:
                            missing_list = "".join([f"<li>{m}</li>" for m in missing])
                            st.markdown(f"""
                                <div style="
                                    background: #FEF3C7; border-left: 4px solid #F59E0B;
                                    padding: 12px; border-radius: 4px; margin: 10px 0;
                                ">
                                    <strong style="color: #B45309;">⚠️ Informations manquantes :</strong>
                                    <ul style="margin: 5px 0 0 15px; padding: 0;">{missing_list}</ul>
                                </div>
                            """, unsafe_allow_html=True)

                        # Bloc uniforme pour Alerte protocole
                        if parsed.get("protocol_alert"):
                            st.markdown(f"""
                                <div style="
                                    background: #FEE2E2; border-left: 4px solid #DC2626;
                                    padding: 12px; border-radius: 4px; margin: 10px 0;
                                ">
                                    <strong style="color: #DC2626;">🚨 Alerte protocole :</strong><br>
                                    {parsed['protocol_alert']}
                                </div>
                            """, unsafe_allow_html=True)

                    except (json.JSONDecodeError, TypeError):
                        st.code(str(raw))
                else:
                    st.info("Aucune analyse")


def render_simulation_results(results: Dict, nurse_message: str):
    """Affiche les résultats détaillés de la simulation côte à côte."""
    st.markdown("---")
    st.subheader("Résultats du Benchmark")

    render_winner_badge(results)
    render_comparison_chart(results)

    st.markdown("### Réponses des patients simulés")
    st.info(f"**Question de l'infirmier :** {nurse_message}")

    valid_results = sort_results_by_model_size({k: v for k, v in results.items() if v.get("success")})
    cols = st.columns(len(valid_results))

    for col_idx, (_, data) in enumerate(valid_results.items()):
        with cols[col_idx]:
            with st.container(border=True):
                render_compact_metrics(data)

                response = data.get("raw_response", "")
                if response:
                    st.markdown(f"""
                        <div style="
                            background: #F3F4F6; padding: 15px;
                            border-radius: 8px; font-style: italic;
                            margin: 10px 0;
                        ">"{response}"</div>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("Pas de réponse")


def main():
    """Point d'entrée principal."""
    init_benchmark_state()

    st.title("🌱 Benchmark Éco-Performance")
    st.caption("Comparez les modèles Mistral et trouvez le plus sobre énergétiquement")

    with st.container(border=True):
        st.markdown("""
        **Objectif :** Comparer les modèles Mistral sur 3 cas d'usage
        pour identifier le meilleur équilibre entre performance et sobriété énergétique.

        Sélectionnez les modèles à comparer puis lancez le benchmark.
        """)

    # Bouton Réinitialiser en haut à droite
    col_spacer, col_reset = st.columns([5, 1])
    with col_reset:
        if st.button("🔄 Réinitialiser", type="secondary", use_container_width=True):
            reset_benchmark_state()
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 Extraction", "🤖 Agent Triage", "💬 Simulation"])

    # === ONGLET EXTRACTION ===
    with tab1:
        st.markdown("### Extraction de données médicales")
        st.caption("Compare l'extraction d'informations structurées depuis une conversation")

        conversations = load_conversations()

        if not conversations:
            st.error("Impossible de charger les conversations. Vérifiez la connexion au backend.")
        else:
            conv_options = {c["filename"]: f"{c['name']} ({c['niveau']})" for c in conversations}
            selected_conv = st.selectbox(
                "Conversation de test",
                options=list(conv_options.keys()),
                format_func=lambda x: conv_options[x],
                key="extraction_conv"
            )

            st.markdown("")
            selected_models = render_model_selector("extraction")

            st.markdown("")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                btn_disabled = len(selected_models) < 2
                if st.button(
                    "🚀 Lancer le benchmark",
                    type="primary",
                    disabled=btn_disabled,
                    use_container_width=True,
                    key="run_extraction"
                ):
                    conv_data = load_conversation_content(selected_conv)
                    if conv_data:
                        full_text = "\n".join([
                            f"{'Infirmier' if m['role'] == 'infirmier' else 'Patient'} : {m['content']}"
                            for m in conv_data.get("messages", [])
                        ])
                        progress = st.empty()
                        results = run_extraction_benchmark(selected_models, full_text, progress)
                        progress.empty()
                        st.session_state.benchmark_results["extraction"] = results
                        st.rerun()

            if btn_disabled:
                st.info("Sélectionnez au moins 2 modèles pour comparer")

            if "extraction" in st.session_state.benchmark_results:
                render_extraction_results(st.session_state.benchmark_results["extraction"])

    # === ONGLET AGENT ===
    with tab2:
        st.markdown("### Agent de Triage")
        st.caption("Compare l'analyse et la classification de criticité")

        conversations = load_conversations()

        if not conversations:
            st.error("Impossible de charger les conversations.")
        else:
            conv_options = {c["filename"]: f"{c['name']} ({c['niveau']})" for c in conversations}
            selected_conv = st.selectbox(
                "Conversation de test",
                options=list(conv_options.keys()),
                format_func=lambda x: conv_options[x],
                key="agent_conv"
            )

            st.markdown("")
            selected_models = render_model_selector("agent")

            st.markdown("")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                btn_disabled = len(selected_models) < 2
                if st.button(
                    "🚀 Lancer le benchmark",
                    type="primary",
                    disabled=btn_disabled,
                    use_container_width=True,
                    key="run_agent"
                ):
                    conv_data = load_conversation_content(selected_conv)
                    if conv_data:
                        progress = st.empty()
                        results = run_agent_benchmark(selected_models, conv_data, progress)
                        progress.empty()
                        st.session_state.benchmark_results["agent"] = results
                        st.rerun()

            if btn_disabled:
                st.info("Sélectionnez au moins 2 modèles pour comparer")

            if "agent" in st.session_state.benchmark_results:
                render_agent_results(st.session_state.benchmark_results["agent"])

    # === ONGLET SIMULATION ===
    with tab3:
        st.markdown("### Simulation Patient")
        st.caption("Compare la génération de réponses patient réalistes")

        sim_options = {k: v["name"] for k, v in SIMULATION_CASES.items()}
        selected_sim = st.selectbox(
            "Cas de simulation",
            options=list(sim_options.keys()),
            format_func=lambda x: sim_options[x],
            key="simulation_case"
        )

        sim_case = SIMULATION_CASES[selected_sim]

        with st.expander("Voir le profil du patient"):
            st.markdown(f"```\n{sim_case['persona']}\n```")

        # Choix de la question de l'infirmier
        selected_question = st.selectbox(
            "Question de l'infirmier",
            options=sim_case["questions"],
            key="nurse_question"
        )

        st.markdown("")
        selected_models = render_model_selector("simulation")

        st.markdown("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            btn_disabled = len(selected_models) < 2
            if st.button(
                "🚀 Lancer le benchmark",
                type="primary",
                disabled=btn_disabled,
                use_container_width=True,
                key="run_simulation"
            ):
                progress = st.empty()
                results = run_simulation_benchmark(selected_models, sim_case, selected_question, progress)
                progress.empty()
                st.session_state.benchmark_results["simulation"] = results
                st.session_state.benchmark_results["simulation_question"] = selected_question
                st.rerun()

        if btn_disabled:
            st.info("Sélectionnez au moins 2 modèles pour comparer")

        if "simulation" in st.session_state.benchmark_results:
            render_simulation_results(
                st.session_state.benchmark_results["simulation"],
                st.session_state.benchmark_results.get("simulation_question", selected_question)
            )

    # Footer avec justification Mistral
    st.markdown("---")
    with st.expander("ℹ️ Pourquoi uniquement des modèles Mistral ?"):
        st.markdown("""
        **Choix de Mistral AI pour ce benchmark :**

        1. **Comparaison équitable** : En utilisant des modèles du même fournisseur, on élimine les biais
           liés aux différences d'infrastructure, de tokenisation et de mesure.

        2. **Support EcoLogits** : La bibliothèque EcoLogits que nous utilisons pour les mesures
           environnementales est optimisée pour les modèles Mistral.

        3. **Souveraineté européenne** : Mistral AI est une entreprise française, ce qui s'aligne
           avec les enjeux de souveraineté numérique en santé.

        4. **Rapport qualité/prix** : Les modèles Mistral offrent un excellent compromis entre
           performance et coût, adapté à un contexte hospitalier.

        5. **Gamme complète** : De Ministral 3B (ultra-léger) à Mistral Large (haute précision),
           la gamme permet de tester différents niveaux de compromis.

        *Pour étendre à d'autres fournisseurs (OpenAI, Anthropic), il faudrait standardiser
        les métriques environnementales, ce qui reste un défi technique.*
        """)


if __name__ == "__main__":
    main()
