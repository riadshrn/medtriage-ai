"""
Page Mode Interactif - Simulation de triage aux urgences.

Cette page permet à un utilisateur (infirmier IOA) de s'entraîner
au triage en interagissant avec un patient simulé par LLM.
"""

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import requests
import streamlit as st

# Configuration des chemins
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from state import init_session_state
from style import apply_style

# Initialisation
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://api:8000")

# Constante pour le seuil de confiance
CONFIDENCE_THRESHOLD = 0.70


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

            # Ne pas marquer comme extrait si c'est une liste vide ou None
            if value is not None and value != [] and value != "":
                self.items[checklist_key].extracted = True
                # Formater la valeur pour l'affichage
                if isinstance(value, list):
                    self.items[checklist_key].value = ", ".join(str(v) for v in value) if value else None
                else:
                    self.items[checklist_key].value = str(value)

    def get_missing_items(self) -> List[str]:
        return [item.label for item in self.items.values() if not item.extracted]

    def get_completion_percentage(self) -> float:
        if not self.items:
            return 0.0
        extracted_count = sum(1 for item in self.items.values() if item.extracted)
        return (extracted_count / len(self.items)) * 100


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
            timeout=3
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
            timeout=3
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
        "Âge": "Quel âge avez-vous ?",
        "Sexe": "Êtes-vous monsieur ou madame ?",
        "Motif": "Qu'est-ce qui vous amène aux urgences ?",
        "Douleur (EVA)": "Sur 10, comment évaluez-vous votre douleur ?",
        "Température": "Avez-vous de la fièvre ?",
        "Fréq. cardiaque": "Ressentez-vous des palpitations ?",
        "Pression artérielle": "Connaissez-vous votre tension ?",
        "Fréq. respiratoire": "Avez-vous du mal à respirer ?",
        "SpO2": "Vous sentez-vous essoufflé ?",
        "Antécédents": "Avez-vous des maladies connues ?",
        "Durée symptômes": "Depuis quand avez-vous ces symptômes ?",
    }

    suggestions = []
    for item in missing[:3]:
        if item in question_templates:
            suggestions.append(question_templates[item])

    return suggestions if suggestions else ["Comment vous sentez-vous ?"]


def request_triage_help(extracted_data: Dict) -> Optional[Dict]:
    """Demande une aide au triage."""
    try:
        response = requests.post(
            f"{API_URL}/triage/evaluate",
            json=extracted_data,
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_triage_color(level: str) -> str:
    colors = {"ROUGE": "#dc3545", "JAUNE": "#ffc107", "VERT": "#28a745", "GRIS": "#6c757d"}
    return colors.get(level, "#6c757d")


def get_triage_emoji(level: str) -> str:
    emojis = {"ROUGE": "🔴", "JAUNE": "🟡", "VERT": "🟢", "GRIS": "⚪"}
    return emojis.get(level, "⚪")


def render_sidebar_checklist() -> None:
    """Affiche la checklist de triage dans la sidebar avec un design amélioré."""
    checklist = st.session_state.triage_checklist
    completion = checklist.get_completion_percentage()

    st.sidebar.markdown("### 📋 Informations collectées")

    # Barre de progression avec couleur
    progress_color = "#28a745" if completion >= 70 else "#ffc107" if completion >= 40 else "#dc3545"
    st.sidebar.markdown(
        f"""<div style="background:#e9ecef;border-radius:10px;height:8px;margin:10px 0;">
            <div style="background:{progress_color};width:{completion}%;height:100%;border-radius:10px;"></div>
        </div>
        <p style="text-align:center;color:#666;font-size:0.85em;">{completion:.0f}% complété</p>""",
        unsafe_allow_html=True
    )

    # Affichage des items en deux colonnes
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
    st.sidebar.markdown("### 🏥 Niveau de Triage")

    # Conditions pour afficher le triage automatiquement
    n_messages = len(st.session_state.simulation_messages)
    completion = st.session_state.triage_checklist.get_completion_percentage()
    should_show = n_messages >= 6 or completion >= 50

    # Calcul du triage si pas encore fait et conditions remplies
    if not st.session_state.triage_result and st.session_state.extracted_data and should_show:
        result = request_triage_help(st.session_state.extracted_data)
        if result:
            st.session_state.triage_result = result

    # Recalculer si données mises à jour
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
        color = get_triage_color(level)

        st.sidebar.markdown(
            f"""<div style="background:{color};color:white;padding:20px;border-radius:12px;text-align:center;margin:10px 0;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="margin:0;font-size:2em;">{emoji} {level}</h2>
                <p style="margin:8px 0 0 0;font-size:1.1em;">{french_level}</p>
                <p style="margin:5px 0 0 0;font-size:0.9em;opacity:0.9;">Confiance: {confidence:.0f}%</p>
            </div>""",
            unsafe_allow_html=True
        )

        if result.get("delai_prise_en_charge"):
            st.sidebar.info(f"⏱️ {result['delai_prise_en_charge']}")

        if result.get("red_flags"):
            st.sidebar.error("**🚨 Alertes:**")
            for alert in result["red_flags"]:
                st.sidebar.markdown(f"• {alert}")

        if result.get("recommendations"):
            with st.sidebar.expander("📋 Recommandations"):
                for rec in result["recommendations"]:
                    st.markdown(f"• {rec}")
    else:
        st.sidebar.info("💡 Le triage s'affichera après 3 échanges ou 50% d'infos collectées")

        if st.sidebar.button("Évaluer maintenant", use_container_width=True):
            if st.session_state.extracted_data:
                result = request_triage_help(st.session_state.extracted_data)
                if result:
                    st.session_state.triage_result = result
                    st.rerun()


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
        st.markdown("**💡 Questions suggérées** *(cliquez pour utiliser)*")
        cols = st.columns(min(len(suggestions), 3))
        for idx, (col, suggestion) in enumerate(zip(cols, suggestions[:3])):
            with col:
                if st.button(suggestion, key=f"sugg_{idx}", use_container_width=True):
                    st.session_state.pending_message = suggestion
                    st.rerun()


def render_chat_interface() -> None:
    """Affiche l'interface de chat."""
    chat_container = st.container(height=380, border=True)

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
            st.info("👋 Posez votre première question au patient pour commencer.")


def process_nurse_message(message: str) -> None:
    """Traite un message de l'infirmier et génère la réponse du patient."""
    # Ajouter le message de l'infirmier
    st.session_state.simulation_messages.append({"role": "user", "content": message})

    # Générer la réponse du patient
    patient_response = call_patient_simulation(
        st.session_state.patient_persona,
        st.session_state.simulation_messages,
        message
    )

    if patient_response is None:
        patient_response = generate_fallback_response(message)

    # Simuler un délai de frappe (effet naturel)
    time.sleep(0.5)

    st.session_state.simulation_messages.append({"role": "assistant", "content": patient_response})

    # Analyser la conversation en arrière-plan
    analysis = analyze_conversation(st.session_state.simulation_messages)
    if analysis and "extracted_data" in analysis:
        st.session_state.extracted_data = analysis["extracted_data"]
        st.session_state.triage_checklist.update_from_analysis(analysis["extracted_data"])

    # Mettre à jour les suggestions
    st.session_state.suggested_questions = generate_question_suggestions(
        st.session_state.triage_checklist,
        st.session_state.simulation_messages
    )


def generate_fallback_response(nurse_message: str) -> str:
    """Génère une réponse de secours si l'API n'est pas disponible."""
    nurse_lower = nurse_message.lower()

    responses = {
        # Identité
        ("âge", "ans", "quel âge"): "J'ai 52 ans.",
        ("homme", "femme", "monsieur", "madame", "sexe"): "Je suis monsieur.",
        # Motif et symptômes
        ("amène", "problème", "urgence", "pourquoi", "motif"): "J'ai une douleur intense dans la poitrine qui m'inquiète beaucoup.",
        ("douleur", "mal", "0 à 10", "sur 10", "eva", "intensité"): "La douleur est vraiment forte, je dirais 8 sur 10.",
        ("depuis", "quand", "combien de temps", "durée", "commencé"): "Ça a commencé il y a environ 2 heures, d'un coup.",
        # Constantes vitales - le patient les "connait" car on vient de les prendre
        ("tension", "pression", "artérielle"): "L'infirmière vient de la prendre, elle a dit 155 sur 95.",
        ("pouls", "coeur", "cardiaque", "battement", "fréquence card"): "Mon coeur bat vite, environ 110 battements par minute d'après l'appareil.",
        ("température", "fièvre", "temp"): "On m'a pris la température, j'ai 37.2°C, pas de fièvre.",
        ("respir", "souffle", "essouffl", "fréquence resp"): "Je respire vite, environ 22 fois par minute, j'ai du mal.",
        ("saturation", "oxygène", "spo2", "satu"): "L'appareil au doigt indique 94%.",
        ("conscience", "glasgow", "orienté", "lucide"): "Je suis conscient et je sais où je suis, mais je suis très anxieux.",
        ("glycémie", "sucre", "diabète"): "Je suis diabétique, ma glycémie était à 1.8 g/L ce matin.",
        # Antécédents
        ("antécédent", "maladie", "problème de santé", "pathologie"): "J'ai du diabète de type 2 et de l'hypertension depuis 10 ans.",
        ("médicament", "traitement", "prenez"): "Je prends de la metformine, un antihypertenseur et de l'aspirine.",
        ("allergie",): "Non, je n'ai pas d'allergie connue.",
        ("opération", "chirurgie", "hospitalisation"): "J'ai été opéré de l'appendicite il y a 20 ans, rien d'autre.",
        ("famille", "hérédité", "parent"): "Mon père a fait un infarctus à 60 ans.",
        # Autres
        ("fum", "tabac", "cigarette"): "Oui, je fume un paquet par jour depuis 30 ans.",
        ("alcool", "boire"): "Je bois un verre de vin le soir, pas plus.",
    }

    for keywords, response in responses.items():
        if any(kw in nurse_lower for kw in keywords):
            return response

    return "Je ne me sens vraiment pas bien... Cette douleur dans la poitrine m'inquiète beaucoup."


def main() -> None:
    """Point d'entrée principal de la page Mode Interactif."""
    init_simulation_state()

    st.title("🎭 Mode Interactif")
    st.caption("Entraînez-vous au triage en interrogeant un patient simulé")

    # --- SIDEBAR ---
    with st.sidebar:
        render_sidebar_checklist()
        render_triage_help()

        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Réinitialiser", use_container_width=True):
            for key in ["simulation_messages", "triage_checklist", "extracted_data",
                       "suggested_questions", "triage_result", "simulation_started", "pending_message"]:
                if key == "triage_checklist":
                    st.session_state[key] = TriageChecklist()
                elif key == "simulation_started":
                    st.session_state[key] = False
                else:
                    st.session_state[key] = [] if "messages" in key or "suggestions" in key else {} if "data" in key else None
            st.rerun()

    # --- CONFIGURATION DU PATIENT ---
    with st.expander("🎭 Configuration du Patient", expanded=not st.session_state.simulation_started):
        default_persona = """Tu es un patient de 52 ans, homme, aux urgences pour douleur thoracique depuis 2h.
ANTÉCÉDENTS: Diabète type 2, hypertension. Tu fumes 1 paquet/jour.
Tu es anxieux et inquiet."""

        st.session_state.patient_persona = st.text_area(
            "Persona du patient",
            value=st.session_state.patient_persona or default_persona,
            height=120,
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("▶️ Démarrer", type="primary", use_container_width=True):
                st.session_state.simulation_started = True
                st.rerun()

        with col2:
            preset = st.selectbox(
                "Cas prédéfinis",
                ["Personnalisé", "Douleur thoracique (ROUGE)", "Détresse respiratoire (ROUGE)",
                 "Traumatisme crânien (JAUNE)", "Douleur abdominale (JAUNE)", "Entorse cheville (VERT)"],
                label_visibility="collapsed"
            )
            presets = {
                "Douleur thoracique (ROUGE)": """Tu es un patient de 58 ans, homme, fumeur (30 ans). Douleur thoracique intense irradiant vers le bras gauche depuis 1h. Tu transpires et as des nausées.
ANTÉCÉDENTS: Hypertension, cholestérol. Père décédé d'infarctus à 55 ans.
Tu es très anxieux, tu as peur de mourir.""",
                "Détresse respiratoire (ROUGE)": """Tu es une patiente de 45 ans, asthmatique connue. Crise sévère depuis 30min, tu parles difficilement.
ANTÉCÉDENTS: Asthme sévère, nombreuses hospitalisations. Tu n'as pas pris ton traitement depuis 2 jours.
Tu es paniquée, tu n'arrives pas à reprendre ton souffle.""",
                "Traumatisme crânien (JAUNE)": """Tu es un patient de 25 ans, chute de vélo il y a 30min. Mal à la tête, un peu confus, bosse sur le front. Tu ne te souviens pas bien de l'accident.
ANTÉCÉDENTS: Aucun.
Tu as des nausées et la lumière te gêne.""",
                "Douleur abdominale (JAUNE)": """Tu es une patiente de 35 ans, douleur abdominale intense en fosse iliaque droite depuis 12h. Fièvre et nausées depuis ce matin.
ANTÉCÉDENTS: Aucun antécédent notable.
Tu as mal quand on appuie sur le ventre à droite et tu n'as pas pu manger.""",
                "Entorse cheville (VERT)": """Tu es un patient de 28 ans, entorse de la cheville droite en jouant au foot il y a 2h. Tu boites mais tu peux marcher.
ANTÉCÉDENTS: Aucun.
Tu es de bonne humeur malgré la douleur, tu veux juste une radio pour être sûr.""",
            }
            if preset != "Personnalisé" and preset in presets:
                st.session_state.patient_persona = presets[preset]
                st.rerun()

    # --- ZONE DE CHAT ---
    if st.session_state.simulation_started:
        st.markdown("---")

        render_question_suggestions()
        st.markdown("")
        render_chat_interface()

        # Traiter un message en attente (depuis les suggestions)
        if st.session_state.pending_message:
            process_nurse_message(st.session_state.pending_message)
            st.session_state.pending_message = None
            st.rerun()

        # Zone de saisie avec st.chat_input (supporte Entrée nativement)
        if user_input := st.chat_input("Posez une question au patient...", key="chat_input"):
            process_nurse_message(user_input)
            st.rerun()

    else:
        st.info("👆 Configurez le patient puis cliquez sur **Démarrer** pour commencer la simulation.")


if __name__ == "__main__":
    main()
