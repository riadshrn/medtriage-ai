"""
Page Mode Interactif - Simulation de triage aux urgences.

Cette page permet à un utilisateur (infirmier IOA) de s'entraîner
au triage en interagissant avec un patient simulé par LLM.
"""

import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# Configuration des chemins
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from state import init_session_state
from style import apply_style, render_triage_badge

# Initialisation
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://backend:8000")

# Constantes
CONFIDENCE_THRESHOLD = 0.70
MIN_FIELDS_FOR_TRIAGE = 5  # Minimum de champs pour activer le bouton triage

# Champs requis pour le ML
REQUIRED_ML_FIELDS = {
    "age", "sexe", "motif_consultation",
    "frequence_cardiaque", "pression_systolique", "temperature"
}


@dataclass
class ChecklistItem:
    """Représente un élément de la checklist de triage."""
    name: str
    label: str
    extracted: bool = False
    value: Optional[str] = None


@dataclass
class TriageChecklist:
    """Checklist des informations à collecter pour le triage."""
    items: Dict[str, ChecklistItem] = field(default_factory=dict)

    def __post_init__(self) -> None:
        default_items = [
            ("age", "Âge"),
            ("sexe", "Sexe"),
            ("motif", "Motif"),
            ("douleur", "Douleur (EVA)"),
            ("temperature", "Température"),
            ("fc", "Fréq. cardiaque"),
            ("pa", "Pression artérielle"),
            ("fr", "Fréq. respiratoire"),
            ("spo2", "SpO2"),
            ("antecedents", "Antécédents"),
            ("duree_symptomes", "Durée symptômes"),
        ]
        for key, label in default_items:
            self.items[key] = ChecklistItem(name=key, label=label)

    def update_from_analysis(self, extracted_data: Dict) -> None:
        mapping = {
            "age": "age",
            "sexe": "sexe",
            "motif": "motif_consultation",
            "douleur": ("constantes", "echelle_douleur"),
            "temperature": ("constantes", "temperature"),
            "fc": ("constantes", "frequence_cardiaque"),
            "pa": ("constantes", "pression_systolique"),
            "fr": ("constantes", "frequence_respiratoire"),
            "spo2": ("constantes", "saturation_oxygene"),
            "antecedents": "antecedents",
            "duree_symptomes": "duree_symptomes",
        }

        for checklist_key, data_path in mapping.items():
            if checklist_key not in self.items:
                continue

            value = None
            if isinstance(data_path, tuple):
                parent, child = data_path
                if parent in extracted_data and extracted_data[parent]:
                    value = extracted_data[parent].get(child)
            else:
                value = extracted_data.get(data_path)

            if value is not None and value != [] and value != "":
                self.items[checklist_key].extracted = True
                if isinstance(value, list):
                    self.items[checklist_key].value = ", ".join(str(v) for v in value) if value else None
                else:
                    self.items[checklist_key].value = str(value)

    def get_missing_items(self) -> List[str]:
        return [item.label for item in self.items.values() if not item.extracted]

    def get_extracted_count(self) -> int:
        return sum(1 for item in self.items.values() if item.extracted)

    def get_completion_percentage(self) -> float:
        if not self.items:
            return 0.0
        return (self.get_extracted_count() / len(self.items)) * 100


def init_simulation_state() -> None:
    """Initialise l'état de la session pour la simulation."""
    defaults = {
        "simulation_messages": [],
        "patient_persona": "",
        "triage_checklist": TriageChecklist(),
        "extracted_data": {},
        "suggested_questions": [],
        "triage_result": None,
        "simulation_started": False,
        "pending_message": None,
        "triage_launched": False,
        "final_triage_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def call_patient_simulation(persona: str, messages: List[Dict], nurse_message: str) -> Optional[str]:
    """Appelle l'API pour générer une réponse du patient simulé."""
    try:
        response = requests.post(
            f"{API_URL}/simulation/patient-response",
            json={"persona": persona, "history": messages, "nurse_message": nurse_message},
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("response")
    except requests.RequestException:
        pass
    return None


def analyze_conversation(messages: List[Dict]) -> Optional[Dict]:
    """Analyse la conversation pour extraire les informations médicales."""
    try:
        full_text = "\n".join([
            f"{'Infirmier' if m['role'] == 'user' else 'Patient'}: {m['content']}"
            for m in messages
        ])
        response = requests.post(
            f"{API_URL}/simulation/extraction/analyze",
            json={"text": full_text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def generate_question_suggestions(checklist: TriageChecklist, messages: List[Dict]) -> List[str]:
    """Génère des suggestions de questions basées sur les informations manquantes."""
    missing = checklist.get_missing_items()
    if not missing:
        return ["Avez-vous d'autres symptômes ?", "Y a-t-il autre chose ?", "Comment vous sentez-vous maintenant ?"]

    question_templates = {
        "Motif": "Qu'est-ce qui vous amène aux urgences ?",
        "Durée symptômes": "Depuis quand avez-vous ces symptômes ?",
        "Douleur (EVA)": "Sur une échelle de 0 à 10, comment évaluez-vous votre douleur ?",
        "Antécédents": "Avez-vous des maladies connues ou des antécédents médicaux ?",
        "Âge": "Quel âge avez-vous ?",
        "Sexe": "Comment dois-je m'adresser à vous ?",
        "Température": "Avez-vous de la fièvre ?",
        "Fréq. cardiaque": "Ressentez-vous des palpitations ?",
        "Pression artérielle": "Connaissez-vous votre tension habituelle ?",
        "Fréq. respiratoire": "Avez-vous du mal à respirer ?",
        "SpO2": "Vous sentez-vous essoufflé ?",
    }

    priority_order = [
        "Motif", "Durée symptômes", "Douleur (EVA)", "Antécédents",
        "Âge", "Sexe", "Température", "Fréq. cardiaque",
        "Pression artérielle", "Fréq. respiratoire", "SpO2",
    ]

    suggestions = []
    for item in priority_order:
        if item in missing and item in question_templates:
            suggestions.append(question_templates[item])
            if len(suggestions) >= 3:
                break

    return suggestions if suggestions else ["Comment vous sentez-vous ?"]


def request_triage_help(extracted_data: Dict) -> Optional[Dict]:
    """Demande une aide au triage (évaluation rapide)."""
    try:
        response = requests.post(
            f"{API_URL}/triage/evaluate",
            json=extracted_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def launch_full_triage(extracted_data: Dict) -> Optional[Dict]:
    """Lance le triage complet via l'API."""
    try:
        # Utiliser /triage/evaluate qui est plus tolérant avec les données manquantes
        response = requests.post(
            f"{API_URL}/triage/evaluate",
            json=extracted_data,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API ({response.status_code}): {response.text}")
    except requests.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
    return None


def save_triage_to_history(result: Dict, extracted_data: Dict) -> Optional[str]:
    """Sauvegarde le triage dans l'historique via l'API."""
    try:
        payload = {
            "source": "simulation",
            "filename": None,
            "gravity_level": result.get("gravity_level", "GRIS"),
            "french_triage_level": result.get("french_triage_level"),
            "confidence_score": result.get("confidence_score"),
            "orientation": result.get("orientation"),
            "delai_prise_en_charge": result.get("delai_prise_en_charge"),
            "extracted_data": extracted_data,
            "model_version": result.get("model_version", "hybrid-v1"),
            "ml_available": result.get("ml_available", True),
            "justification": result.get("justification"),
            "red_flags": result.get("red_flags"),
            "recommendations": result.get("recommendations")
        }
        response = requests.post(f"{API_URL}/history/save", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("prediction_id")
    except requests.RequestException as e:
        st.warning(f"Impossible de sauvegarder dans l'historique: {e}")
    return None


def get_triage_color(level: str) -> str:
    colors = {"ROUGE": "#dc3545", "JAUNE": "#ffc107", "VERT": "#28a745", "GRIS": "#6c757d"}
    return colors.get(level, "#6c757d")


def get_triage_emoji(level: str) -> str:
    emojis = {"ROUGE": "🔴", "JAUNE": "🟡", "VERT": "🟢", "GRIS": "⚪"}
    return emojis.get(level, "⚪")


def build_json_display(extracted_data: Dict) -> Dict[str, Any]:
    """Construit un JSON formaté pour l'affichage."""
    constantes = extracted_data.get("constantes", {})

    return {
        "patient": {
            "age": extracted_data.get("age"),
            "sexe": extracted_data.get("sexe"),
            "motif_consultation": extracted_data.get("motif_consultation"),
            "duree_symptomes": extracted_data.get("duree_symptomes"),
        },
        "antecedents": extracted_data.get("antecedents", []),
        "traitements": extracted_data.get("traitements", []),
        "constantes_vitales": {
            "frequence_cardiaque": constantes.get("frequence_cardiaque"),
            "pression_arterielle": f"{constantes.get('pression_systolique')}/{constantes.get('pression_diastolique')}"
                if constantes.get('pression_systolique') else None,
            "frequence_respiratoire": constantes.get("frequence_respiratoire"),
            "temperature": constantes.get("temperature"),
            "saturation_oxygene": constantes.get("saturation_oxygene"),
            "echelle_douleur": constantes.get("echelle_douleur"),
            "glasgow": constantes.get("glasgow"),
        },
        "informations_manquantes": extracted_data.get("missing_critical_info", [])
    }


def can_launch_triage(checklist: TriageChecklist) -> bool:
    """Vérifie si on a assez d'informations pour lancer le triage."""
    extracted_count = checklist.get_extracted_count()
    # Vérifier qu'on a au moins les infos de base
    has_motif = checklist.items.get("motif", ChecklistItem("", "")).extracted
    has_age = checklist.items.get("age", ChecklistItem("", "")).extracted

    return extracted_count >= MIN_FIELDS_FOR_TRIAGE and has_motif and has_age


def render_json_panel() -> None:
    """Affiche le panneau JSON temps réel."""
    st.markdown("### 📋 Données Extraites")

    extracted_data = st.session_state.extracted_data

    if extracted_data:
        json_display = build_json_display(extracted_data)

        # Afficher avec coloration selon les valeurs
        st.json(json_display)

        # Indicateur de complétude
        checklist = st.session_state.triage_checklist
        completion = checklist.get_completion_percentage()
        extracted_count = checklist.get_extracted_count()
        total_count = len(checklist.items)

        st.markdown(f"**Complétude:** {extracted_count}/{total_count} champs ({completion:.0f}%)")

        # Barre de progression
        progress_color = "#28a745" if completion >= 70 else "#ffc107" if completion >= 40 else "#dc3545"
        st.markdown(
            f"""<div style="background:#e9ecef;border-radius:10px;height:10px;margin:10px 0;">
                <div style="background:{progress_color};width:{completion}%;height:100%;border-radius:10px;"></div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.info("Les données apparaîtront ici au fur et à mesure de la conversation.")


def render_sidebar_checklist() -> None:
    """Affiche la checklist de triage dans la sidebar avec un design amélioré."""
    checklist = st.session_state.triage_checklist
    completion = checklist.get_completion_percentage()

    st.sidebar.markdown("### Informations collectées")

    progress_color = "#28a745" if completion >= 70 else "#ffc107" if completion >= 40 else "#dc3545"
    st.sidebar.markdown(
        f"""<div style="background:#e9ecef;border-radius:10px;height:8px;margin:10px 0;">
            <div style="background:{progress_color};width:{completion}%;height:100%;border-radius:10px;"></div>
        </div>
        <p style="text-align:center;color:#666;font-size:0.85em;">{completion:.0f}% complété</p>""",
        unsafe_allow_html=True
    )

    col1, col2 = st.sidebar.columns(2)
    items_list = list(checklist.items.values())
    mid = len(items_list) // 2 + len(items_list) % 2

    for idx, item in enumerate(items_list):
        col = col1 if idx < mid else col2
        with col:
            if item.extracted and item.value:
                st.markdown(f"✅ **{item.label}**<br><span style='color:#28a745;font-size:0.9em;'>{item.value}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"⬜ <span style='color:#999;'>{item.label}</span>", unsafe_allow_html=True)


def render_triage_help() -> None:
    """Affiche le panneau d'aide au triage."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Niveau de Triage")

    n_messages = len(st.session_state.simulation_messages)
    completion = st.session_state.triage_checklist.get_completion_percentage()
    should_show = n_messages >= 6 or completion >= 50

    if not st.session_state.triage_result and st.session_state.extracted_data and should_show:
        result = request_triage_help(st.session_state.extracted_data)
        if result:
            st.session_state.triage_result = result

    elif st.session_state.triage_result and st.session_state.extracted_data:
        new_result = request_triage_help(st.session_state.extracted_data)
        if new_result:
            st.session_state.triage_result = new_result

    if st.session_state.triage_result:
        result = st.session_state.triage_result
        level = result.get("gravity_level", "GRIS")
        french_level = result.get("french_triage_level", "Tri 5")
        confidence = result.get("confidence_score", 0) * 100
        emoji = get_triage_emoji(level)

        # Badge de triage avec les nouvelles classes CSS
        css_class = f"triage-{level.lower()}"
        st.sidebar.markdown(
            f"""<div class="triage-badge {css_class}" style="padding:15px;">
                <div style="font-size:1.8em;margin-bottom:5px;">{emoji} {level}</div>
                <div style="font-size:1em;opacity:0.95;">{french_level}</div>
                <div style="font-size:0.85em;opacity:0.8;margin-top:5px;">Confiance: {confidence:.0f}%</div>
            </div>""",
            unsafe_allow_html=True
        )

        if result.get("delai_prise_en_charge"):
            st.sidebar.info(f"⏱️ {result['delai_prise_en_charge']}")
    else:
        st.sidebar.info("Le triage s'affichera après 3 échanges ou 50% d'infos collectées")

        if st.sidebar.button("Évaluer maintenant", use_container_width=True):
            if st.session_state.extracted_data:
                result = request_triage_help(st.session_state.extracted_data)
                if result:
                    st.session_state.triage_result = result
                    st.rerun()


def send_suggestion(suggestion: str) -> None:
    """Callback pour envoyer une question suggérée."""
    st.session_state.pending_message = suggestion


def render_question_suggestions() -> None:
    """Affiche les boutons de suggestions de questions."""
    suggestions = st.session_state.suggested_questions
    if not suggestions:
        suggestions = generate_question_suggestions(
            st.session_state.triage_checklist,
            st.session_state.simulation_messages
        )
        st.session_state.suggested_questions = suggestions

    if suggestions:
        st.markdown("**Questions suggérées** *(cliquez pour utiliser)*")
        cols = st.columns(min(len(suggestions), 3))
        for idx, (col, suggestion) in enumerate(zip(cols, suggestions[:3])):
            with col:
                st.button(
                    suggestion,
                    key=f"sugg_{idx}",
                    use_container_width=True,
                    on_click=send_suggestion,
                    args=(suggestion,)
                )


def render_chat_interface() -> None:
    """Affiche l'interface de chat."""
    chat_container = st.container(height=350, border=True)

    with chat_container:
        if st.session_state.simulation_messages:
            for msg in st.session_state.simulation_messages:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="🧑‍⚕️"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🤒"):
                        st.write(msg["content"])
        else:
            st.info("Posez votre première question au patient pour commencer.")


def process_nurse_message(message: str) -> None:
    """Traite un message de l'infirmier et génère la réponse du patient."""
    st.session_state.simulation_messages.append({"role": "user", "content": message})

    with st.spinner("Le patient réfléchit..."):
        patient_response = call_patient_simulation(
            st.session_state.patient_persona,
            st.session_state.simulation_messages,
            message
        )

        if patient_response is None:
            patient_response = generate_fallback_response(message)

    st.session_state.simulation_messages.append({"role": "assistant", "content": patient_response})

    with st.spinner("Analyse en cours..."):
        analysis = analyze_conversation(st.session_state.simulation_messages)
        if analysis and "extracted_data" in analysis:
            st.session_state.extracted_data = analysis["extracted_data"]
            st.session_state.triage_checklist.update_from_analysis(analysis["extracted_data"])

            # Accumuler les métriques pour le triage en cours (groupées par triage)
            m = analysis.get("metrics")
            if m:
                acc = st.session_state['current_interactive_session_metrics']
                acc['cost_usd'] += m.get('cost_usd', 0) or 0
                acc['gwp_kgco2'] += m.get('gwp_kgco2', 0) or 0
                acc['energy_kwh'] += m.get('energy_kwh', 0) or 0
                acc['nb_calls'] += 1
                # Mettre à jour la dernière requête (toutes sources)
                st.session_state['last_request_metrics'] = m
                st.session_state['last_request_source'] = "Mode Interactif"

    st.session_state.suggested_questions = generate_question_suggestions(
        st.session_state.triage_checklist,
        st.session_state.simulation_messages
    )


def generate_fallback_response(nurse_message: str) -> str:
    """Génère une réponse de secours si l'API n'est pas disponible."""
    nurse_lower = nurse_message.lower()

    responses = {
        ("âge", "ans", "quel âge"): "J'ai 52 ans.",
        ("homme", "femme", "monsieur", "madame", "sexe"): "Je suis monsieur.",
        ("amène", "problème", "urgence", "pourquoi", "motif"): "J'ai une douleur intense dans la poitrine qui m'inquiète beaucoup.",
        ("douleur", "mal", "0 à 10", "sur 10", "eva", "intensité"): "La douleur est vraiment forte, je dirais 8 sur 10.",
        ("depuis", "quand", "combien de temps", "durée", "commencé"): "Ça a commencé il y a environ 2 heures, d'un coup.",
        ("tension", "pression", "artérielle"): "L'infirmière vient de la prendre, elle a dit 155 sur 95.",
        ("pouls", "coeur", "cardiaque", "battement", "fréquence card"): "Mon coeur bat vite, environ 110 battements par minute d'après l'appareil.",
        ("température", "fièvre", "temp"): "On m'a pris la température, j'ai 37.2°C, pas de fièvre.",
        ("respir", "souffle", "essouffl", "fréquence resp"): "Je respire vite, environ 22 fois par minute, j'ai du mal.",
        ("saturation", "oxygène", "spo2", "satu"): "L'appareil au doigt indique 94%.",
        ("conscience", "glasgow", "orienté", "lucide"): "Je suis conscient et je sais où je suis, mais je suis très anxieux.",
        ("glycémie", "sucre", "diabète"): "Je suis diabétique, ma glycémie était à 1.8 g/L ce matin.",
        ("antécédent", "maladie", "problème de santé", "pathologie"): "J'ai du diabète de type 2 et de l'hypertension depuis 10 ans.",
        ("médicament", "traitement", "prenez"): "Je prends de la metformine, un antihypertenseur et de l'aspirine.",
        ("allergie",): "Non, je n'ai pas d'allergie connue.",
        ("opération", "chirurgie", "hospitalisation"): "J'ai été opéré de l'appendicite il y a 20 ans, rien d'autre.",
        ("famille", "hérédité", "parent"): "Mon père a fait un infarctus à 60 ans.",
        ("fum", "tabac", "cigarette"): "Oui, je fume un paquet par jour depuis 30 ans.",
        ("alcool", "boire"): "Je bois un verre de vin le soir, pas plus.",
    }

    for keywords, response in responses.items():
        if any(kw in nurse_lower for kw in keywords):
            return response

    return "Je ne me sens vraiment pas bien... Cette douleur dans la poitrine m'inquiète beaucoup."


def render_final_triage_result() -> None:
    """Affiche le résultat final du triage."""
    result = st.session_state.final_triage_result

    if not result:
        return

    st.markdown("---")
    st.markdown("## Résultat du Triage")

    level = result.get("gravity_level", "GRIS")
    french_level = result.get("french_triage_level", "Tri 5")
    confidence = result.get("confidence_score", 0) * 100
    emoji = get_triage_emoji(level)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Badge de triage principal avec les nouvelles classes CSS
        css_class = f"triage-{level.lower()}"
        st.markdown(
            f"""<div class="triage-badge {css_class}" style="padding:2rem;">
                <div style="font-size:2.5em;margin-bottom:10px;">{emoji} {level}</div>
                <div style="font-size:1.3em;opacity:0.95;">{french_level}</div>
                <div style="font-size:1em;opacity:0.8;margin-top:10px;">Confiance: {confidence:.0f}%</div>
            </div>""",
            unsafe_allow_html=True
        )

        if result.get("delai_prise_en_charge"):
            st.info(f"⏱️ **Délai de prise en charge:** {result['delai_prise_en_charge']}")

        if result.get("orientation"):
            st.success(f"**Orientation:** {result['orientation']}")

    with col2:
        if result.get("justification"):
            st.markdown("**Justification:**")
            st.write(result["justification"])

        if result.get("red_flags"):
            st.error("**Signaux d'alerte:**")
            for flag in result["red_flags"]:
                st.markdown(f"- {flag}")

        if result.get("recommendations"):
            st.warning("**Recommandations:**")
            for rec in result["recommendations"]:
                st.markdown(f"- {rec}")

    # Bouton pour donner un feedback
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Nouvelle Simulation", use_container_width=True):
            # Reset tout
            for key in ["simulation_messages", "patient_persona", "extracted_data",
                       "suggested_questions", "triage_result", "simulation_started",
                       "pending_message", "triage_launched", "final_triage_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["triage_checklist"] = TriageChecklist()
            # Réinitialiser l'accumulateur de métriques
            st.session_state['current_interactive_session_metrics'] = {
                'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0
            }
            st.rerun()

    with col2:
        if st.button("Donner un Feedback", type="primary", use_container_width=True):
            # Stocker les données pour le feedback
            st.session_state['last_triage_result'] = {
                'prediction_id': result.get('prediction_id', str(uuid.uuid4())),
                'gravity_level': level,
                'french_triage_level': french_level,
                'extracted_data': st.session_state.extracted_data,
                'source': 'simulation'
            }
            st.switch_page("pages/3_Feedback.py")


def main() -> None:
    """Point d'entrée principal de la page Mode Interactif."""
    init_simulation_state()

    st.title("Mode Interactif")
    st.caption("Entraînez-vous au triage en interrogeant un patient simulé")

    # Si le triage final a été lancé, afficher le résultat
    if st.session_state.triage_launched and st.session_state.final_triage_result:
        render_final_triage_result()
        return

    # --- SIDEBAR ---
    with st.sidebar:
        render_sidebar_checklist()
        render_triage_help()

        st.sidebar.markdown("---")
        if st.sidebar.button("Réinitialiser", use_container_width=True):
            for key in ["simulation_messages", "patient_persona", "extracted_data",
                       "suggested_questions", "triage_result", "simulation_started",
                       "pending_message", "triage_launched", "final_triage_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["triage_checklist"] = TriageChecklist()
            # Réinitialiser l'accumulateur de métriques
            st.session_state['current_interactive_session_metrics'] = {
                'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0
            }
            st.rerun()

    # --- CONFIGURATION DU PATIENT ---
    with st.expander("Configuration du Patient", expanded=not st.session_state.simulation_started):
        presets = {
            "Douleur thoracique": """Tu es un patient de 58 ans, homme, fumeur (30 ans). Douleur thoracique intense irradiant vers le bras gauche depuis 1h. Tu transpires et as des nausées.
ANTÉCÉDENTS: Hypertension, cholestérol. Père décédé d'infarctus à 55 ans.
Tu es très anxieux, tu as peur de mourir.""",
            "Détresse respiratoire": """Tu es une patiente de 45 ans, asthmatique connue. Crise sévère depuis 30min, tu parles difficilement.
ANTÉCÉDENTS: Asthme sévère, nombreuses hospitalisations. Tu n'as pas pris ton traitement depuis 2 jours.
Tu es paniquée, tu n'arrives pas à reprendre ton souffle.""",
            "Traumatisme crânien": """Tu es un patient de 25 ans, chute de vélo il y a 30min. Mal à la tête, un peu confus, bosse sur le front. Tu ne te souviens pas bien de l'accident.
ANTÉCÉDENTS: Aucun.
Tu as des nausées et la lumière te gêne.""",
            "Douleur abdominale": """Tu es une patiente de 35 ans, douleur abdominale intense en fosse iliaque droite depuis 12h. Fièvre et nausées depuis ce matin.
ANTÉCÉDENTS: Aucun antécédent notable.
Tu as mal quand on appuie sur le ventre à droite et tu n'as pas pu manger.""",
            "Entorse cheville": """Tu es un patient de 28 ans, entorse de la cheville droite en jouant au foot il y a 2h. Tu boites mais tu peux marcher.
ANTÉCÉDENTS: Aucun.
Tu es de bonne humeur malgré la douleur, tu veux juste une radio pour être sûr.""",
        }

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("**Choisir un cas prédéfini :**")
            preset = st.selectbox(
                "Cas prédéfinis",
                ["-- Sélectionner --"] + list(presets.keys()),
                label_visibility="collapsed"
            )
            if preset != "-- Sélectionner --" and preset in presets:
                st.session_state.patient_persona = presets[preset]

        with col2:
            st.markdown("**Ou créer un cas personnalisé :**")
            st.caption("Décrivez le patient (âge, sexe, motif, antécédents...)")

        persona_value = st.text_area(
            "Persona du patient",
            value=st.session_state.patient_persona,
            height=120,
            placeholder="Ex: Tu es un patient de 45 ans, femme, venue pour migraine intense depuis 6h...",
            label_visibility="collapsed"
        )
        st.session_state.patient_persona = persona_value

        can_start = bool(st.session_state.patient_persona.strip())
        if st.button("Démarrer la simulation", type="primary", use_container_width=True, disabled=not can_start):
            st.session_state.simulation_started = True
            st.rerun()

        if not can_start:
            st.warning("Veuillez sélectionner un cas ou décrire un patient personnalisé.")

    # --- ZONE DE CHAT ET JSON ---
    if st.session_state.simulation_started:
        st.markdown("---")

        # Traiter un message en attente
        if st.session_state.pending_message:
            msg_to_send = st.session_state.pending_message
            st.session_state.pending_message = None
            process_nurse_message(msg_to_send)
            st.rerun()

        # Layout principal : Chat à gauche, JSON à droite
        col_chat, col_json = st.columns([3, 2])

        with col_chat:
            render_question_suggestions()
            st.markdown("")
            render_chat_interface()

            # Zone de saisie
            user_input = st.chat_input("Posez une question au patient...")
            if user_input:
                process_nurse_message(user_input)
                st.rerun()

        with col_json:
            render_json_panel()

            # Bouton Lancer le Triage
            st.markdown("---")
            checklist = st.session_state.triage_checklist
            can_triage = can_launch_triage(checklist)

            if can_triage:
                st.success("Vous avez collecté suffisamment d'informations !")
                if st.button("LANCER LE TRIAGE", type="primary", use_container_width=True):
                    with st.spinner("Calcul du triage en cours..."):
                        result = launch_full_triage(st.session_state.extracted_data)
                        if result:
                            # Sauvegarder dans l'historique
                            prediction_id = save_triage_to_history(result, st.session_state.extracted_data)
                            result['prediction_id'] = prediction_id

                            # Ajouter le niveau de triage à l'historique
                            gravity = result.get("gravity_level", "GRIS")
                            st.session_state['interactive_triage_history'].append(gravity)

                            # Ajouter les métriques accumulées de la session au Dashboard (groupé par triage)
                            acc = st.session_state['current_interactive_session_metrics']
                            if acc['nb_calls'] > 0:
                                st.session_state['interactive_metrics_history'].append({
                                    'cost_usd': acc['cost_usd'],
                                    'gwp_kgco2': acc['gwp_kgco2'],
                                    'energy_kwh': acc['energy_kwh'],
                                    'nb_calls': acc['nb_calls']
                                })
                                # Réinitialiser l'accumulateur
                                st.session_state['current_interactive_session_metrics'] = {
                                    'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0
                                }

                            st.session_state.final_triage_result = result
                            st.session_state.triage_launched = True
                            st.rerun()
                        else:
                            st.error("Erreur lors du triage. Vérifiez la connexion à l'API.")
            else:
                missing = checklist.get_missing_items()
                st.warning(f"Collectez plus d'informations ({checklist.get_extracted_count()}/{MIN_FIELDS_FOR_TRIAGE} minimum)")
                st.button("LANCER LE TRIAGE", disabled=True, use_container_width=True)

                with st.expander("Informations manquantes"):
                    for item in missing[:5]:
                        st.markdown(f"- {item}")

    else:
        st.info("Configurez le patient puis cliquez sur **Démarrer** pour commencer la simulation.")


if __name__ == "__main__":
    main()
