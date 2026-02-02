"""
Page Mode Interactif - Simulation de triage aux urgences.
Version Refactorisée : Full Agentic + Feedback Loop.
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import requests
import streamlit as st

# Configuration des chemins
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from state import init_session_state
from style import configure_page, apply_style

# IMPORTANT: configure_page DOIT être appelée EN PREMIER
configure_page(page_title="Mode interactif - MedTriage-AI")
init_session_state()
apply_style()

# Configuration API
API_URL = os.getenv("API_URL", "http://backend:8000")
MIN_FIELDS_FOR_VALIDATION = 4

# Liste stricte alignée sur le backend (med_tools.py)
REQUIRED_FOR_ML = {
    "age", "sexe", 
    "constantes.frequence_cardiaque", 
    "constantes.pression_systolique", 
    "constantes.pression_diastolique", 
    "constantes.temperature", 
    "constantes.saturation_oxygene", 
    "constantes.frequence_respiratoire"
}

# --- FONCTIONS UTILITAIRES ---

def filter_empty_values(data: Dict) -> Dict:
    """Nettoie le dictionnaire pour l'affichage."""
    if not isinstance(data, dict): return data
    clean_dict = {}
    for k, v in data.items():
        if isinstance(v, dict):
            nested = filter_empty_values(v)
            if nested: clean_dict[k] = nested
        elif isinstance(v, list):
            if v: clean_dict[k] = v
        elif v is not None and v != "":
            clean_dict[k] = v
    return clean_dict

def calculate_ml_completion(data: Dict) -> float:
    """Calcule le pourcentage de complétion ML."""
    if not data: return 0.0
    root = data.get("patient", data)
    constantes = root.get("constantes", root)
    present_count = 0
    for field_path in REQUIRED_FOR_ML:
        val = None
        if "constantes." in field_path:
            key = field_path.split(".")[1]
            val = constantes.get(key)
        else:
            val = root.get(field_path)
        if val is not None and val != "" and val != []:
            present_count += 1
    return (present_count / len(REQUIRED_FOR_ML)) * 100

def get_triage_emoji(level: str) -> str:
    emojis = {"ROUGE": "🔴", "JAUNE": "🟡", "VERT": "🟢", "GRIS": "⚪"}
    return emojis.get(level, "⚪")

# --- APPELS API ---

def call_patient_simulation(persona: str, messages: List[Dict], nurse_message: str) -> Optional[str]:
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

def call_agent_interact(messages: List[Dict]) -> Optional[Dict]:
    try:
        full_text = "\n".join([f"{'Infirmier' if m['role'] == 'user' else 'Patient'}: {m['content']}" for m in messages])
        response = requests.post(f"{API_URL}/simulation/agent/interact", json={"text": full_text}, timeout=30)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def save_triage_to_history(result: Dict, extracted_data: Dict, metrics: Dict = None) -> Optional[str]:
    try:
        payload = {
            "source": "simulation",
            "gravity_level": result.get("gravity_level", "GRIS"),
            "french_triage_level": result.get("french_triage_level"),
            "extracted_data": extracted_data,
            "justification": result.get("justification"),
            "red_flags": result.get("red_flags"),
            "recommendations": result.get("recommendations"),
            "metrics": metrics
        }
        response = requests.post(f"{API_URL}/history/save", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("prediction_id")
    except requests.RequestException:
        pass
    return None

# --- LOGIQUE METIER ---

def generate_question_suggestions() -> List[str]:
    data = st.session_state.get("extracted_data", {})
    missing_list = data.get("missing_critical_info", [])
    templates = {
        "temperature": "Avez-vous de la fièvre ?",
        "frequence_cardiaque": "Votre cœur bat-il vite ?",
        "douleur": "Votre douleur est à combien sur 10 ?",
        "duree": "Depuis combien de temps ?",
        "antecedents": "Vos antécédents ?",
        "traitement": "Prenez-vous des médicaments ?",
        "age": "Quel âge avez-vous ?",
        "sexe": "Êtes-vous un homme ou une femme ?",
        "saturation": "Respirez-vous bien ?"
    }
    suggestions = []
    for missing_item in missing_list:
        for key, question in templates.items():
            if key in missing_item.lower() and question not in suggestions:
                suggestions.append(question)
    defaults = ["Décrivez vos symptômes.", "Depuis quand ?", "Antécédents ?"]
    for d in defaults:
        if len(suggestions) < 3 and d not in suggestions: suggestions.append(d)
    return suggestions[:3]

def process_nurse_message(message: str) -> None:
    st.session_state.simulation_messages.append({"role": "user", "content": message})
    with st.spinner("Le patient réfléchit..."):
        patient_resp = call_patient_simulation(st.session_state.patient_persona, st.session_state.simulation_messages, message) or "..."
    st.session_state.simulation_messages.append({"role": "assistant", "content": patient_resp})
    
    with st.spinner("L'IA analyse..."):
        agent_result = call_agent_interact(st.session_state.simulation_messages)
        if agent_result and "extracted_data" in agent_result:
            data = agent_result["extracted_data"]
            if "missing_info" in agent_result: data["missing_critical_info"] = agent_result["missing_info"]
            st.session_state.extracted_data = data
            st.session_state['latest_agent_result'] = agent_result
            
            if "metrics" in agent_result:
                m = agent_result["metrics"]
                acc = st.session_state['current_interactive_session_metrics']
                acc['cost_usd'] += m.get('cost_usd', 0) or 0
                acc['gwp_kgco2'] += m.get('gwp_kgco2', 0) or 0
                acc['energy_kwh'] += m.get('energy_kwh', 0) or 0
                acc['nb_calls'] += 1
                st.session_state['last_request_metrics'] = m
                st.session_state['last_request_source'] = "Mode Interactif"

    st.session_state.suggested_questions = generate_question_suggestions()

# --- UI RENDERING ---

def render_agent_reasoning():
    res = st.session_state.get("latest_agent_result")
    if not res: return
    criticity = res.get("criticity", "GRIS")
    colors = {"ROUGE": "red", "JAUNE": "orange", "VERT": "green", "GRIS": "grey"}
    with st.expander(f"🧠 Raisonnement IA (Triage : :{colors.get(criticity, 'grey')}[{criticity}])", expanded=True):
        for step in res.get("reasoning_steps", []):
            if "Tool Call" in step: st.caption(f"🛠️ {step}")
            elif "Finalisation" in step: st.caption("🏁 Conclusion...")
            else: st.markdown(f"- {step}")

def render_json_panel():
    st.markdown("### 📋 Données Extraites")
    raw = st.session_state.get("extracted_data", {})
    if raw:
        clean = filter_empty_values(raw)
        st.json(clean)
        progress = calculate_ml_completion(raw)
        color, label = ("#28a745", "✅ Dossier complet ML") if progress >= 100 else ("#dc3545", f"❌ Incomplet ML ({int(progress)}%)")
        st.markdown(f"""<div style="background:#e9ecef;border-radius:5px;height:8px;margin-top:5px;"><div style="background:{color};width:{progress}%;height:100%;border-radius:5px;"></div></div><div style="text-align:right;font-size:0.8em;color:#666;">{label}</div>""", unsafe_allow_html=True)
    else:
        st.info("En attente...")

def render_sidebar_summary():
    res = st.session_state.get("latest_agent_result")
    if res:
        lvl = res.get("criticity", "GRIS")
        st.sidebar.markdown("### Estimation Temps Réel")
        st.sidebar.markdown(f"""<div class="triage-badge triage-{lvl.lower()}" style="padding:15px;text-align:center;"><div style="font-size:2em;">{get_triage_emoji(lvl)} {lvl}</div><div style="font-size:0.9em;opacity:0.8;">via Protocole</div></div>""", unsafe_allow_html=True)
        if res.get("protocol_alert"): st.sidebar.warning(f"⚠️ {res['protocol_alert']}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Champs Requis (ML)")
    data = st.session_state.get("extracted_data", {})
    root = data.get("patient", data)
    const = root.get("constantes", root) if isinstance(root.get("constantes"), dict) else {}
    
    for field in sorted(REQUIRED_FOR_ML):
        if "constantes." in field:
            key = field.split(".")[1]
            val = const.get(key)
            label = key.replace("_", " ").capitalize()
        else:
            val = root.get(field)
            label = field.capitalize()
        label = label.replace("Frequence", "Fréq.").replace("Pression", "Tens.").replace("Saturation", "Sat.")
        icon, display = ("✅", f": **{val}**") if (val is not None and val != "" and val != []) else ("⬜", "")
        st.sidebar.markdown(f"{icon} {label}{display}")

def init_simulation_state():
    keys = ["simulation_messages", "patient_persona", "extracted_data", "suggested_questions", "simulation_started", "pending_message", "triage_launched", "final_triage_result"]
    for k in keys:
        if k not in st.session_state: st.session_state[k] = None if k == "pending_message" or k == "final_triage_result" else [] if "messages" in k or "questions" in k else {} if "data" in k else False if "started" in k or "launched" in k else ""
    if "current_interactive_session_metrics" not in st.session_state:
        st.session_state.current_interactive_session_metrics = {'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0}

def main():
    init_simulation_state()
    st.title("Mode Interactif")
    
    if st.session_state.triage_launched and st.session_state.final_triage_result:
        res = st.session_state.final_triage_result
        lvl = res.get("gravity_level", "GRIS")
        french_level = res.get("french_triage_level", "Tri Agent")
        confidence = res.get("confidence_score", 0.75)
        if isinstance(confidence, (int, float)) and confidence <= 1:
            confidence = confidence * 100
        emoji = get_triage_emoji(lvl)

        # Couleurs par niveau
        colors = {
            "ROUGE": ("#dc3545", "#fff", "Urgence Vitale"),
            "JAUNE": ("#ffc107", "#000", "Urgence Relative"),
            "VERT": ("#28a745", "#fff", "Consultation Standard"),
            "GRIS": ("#6c757d", "#fff", "Non Urgent")
        }
        bg_color, text_color, level_desc = colors.get(lvl, ("#6c757d", "#fff", "Non défini"))

        # Grande bannière de triage
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            margin: 1rem 0 2rem 0;
            box-shadow: 0 10px 40px {bg_color}66;
        ">
            <div style="font-size: 4rem; margin-bottom: 0.5rem;">{emoji}</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: {text_color};">{lvl}</div>
            <div style="font-size: 1.3rem; color: {text_color}; opacity: 0.9; margin-top: 0.5rem;">{french_level}</div>
            <div style="font-size: 1rem; color: {text_color}; opacity: 0.8; margin-top: 0.3rem;">{level_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        # Score de confiance avec explication
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Score de Confiance")
            conf_color = "#28a745" if confidence >= 80 else "#ffc107" if confidence >= 60 else "#dc3545"
            st.markdown(f"""
            <div style="background: #1e293b; border-radius: 15px; padding: 1.5rem; text-align: center;">
                <div style="font-size: 2.5rem; font-weight: bold; color: {conf_color};">{confidence:.0f}%</div>
                <div style="background: #334155; border-radius: 10px; height: 12px; margin: 1rem 0;">
                    <div style="background: {conf_color}; width: {confidence}%; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Comment est calculé le score ?"):
                st.markdown("""
                Le **score de confiance** est calculé selon plusieurs critères :

                - **Base** : 75% (protocole FRENCH)
                - **+15%** si le ML confirme le niveau FRENCH
                - **+10%** si red flags détectés → confiance max
                - **-10%** si qualité des données LOW
                - **-20%** si données insuffisantes

                *Formule* : `Confiance = Base + Bonus_ML - Pénalité_Qualité`
                """)

        with col2:
            st.markdown("### Prise en Charge")
            delai = res.get("delai_prise_en_charge", "À évaluer")
            orientation = res.get("orientation", "À déterminer par le médecin")

            st.markdown(f"""
            <div style="background: #1e293b; border-radius: 15px; padding: 1.5rem;">
                <div style="margin-bottom: 1rem;">
                    <div style="color: #94a3b8; font-size: 0.9rem;">⏱️ Délai de prise en charge</div>
                    <div style="color: #fff; font-size: 1.3rem; font-weight: 600;">{delai}</div>
                </div>
                <div>
                    <div style="color: #94a3b8; font-size: 0.9rem;">🏥 Orientation</div>
                    <div style="color: #fff; font-size: 1.3rem; font-weight: 600;">{orientation}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Justification
        st.markdown("### Justification")
        justification = res.get("justification", "Évaluation basée sur le protocole FRENCH et l'analyse de l'agent.")
        st.info(f"📋 {justification}")

        # Signaux d'alerte
        red_flags = res.get("red_flags", [])
        if red_flags:
            st.markdown("### Signaux d'Alerte")
            for flag in red_flags:
                if flag:
                    st.error(f"🚨 {flag}")

        # Recommandations
        recommendations = res.get("recommendations", [])
        if recommendations:
            st.markdown("### Recommandations")
            for rec in recommendations:
                if rec:
                    st.warning(f"💡 {rec}")

        st.markdown("---")

        # Boutons d'action
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nouvelle Simulation", use_container_width=True):
                for k in ["simulation_messages", "patient_persona", "extracted_data", "triage_launched", "final_triage_result", "simulation_started", "latest_agent_result"]:
                    if k in st.session_state: del st.session_state[k]
                st.session_state['current_interactive_session_metrics'] = {'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0}
                st.rerun()
        with col2:
            if st.button("📝 Donner un Feedback", type="primary", use_container_width=True):
                st.session_state['last_triage_result'] = {
                    'prediction_id': res.get('prediction_id') or "sim_unknown",
                    'gravity_level': lvl,
                    'french_triage_level': french_level,
                    'confidence_score': confidence,
                    'extracted_data': st.session_state.extracted_data,
                    'source': 'simulation',
                    'filename': 'Simulation Interactive'
                }
                st.switch_page("pages/3_Feedback.py")
        return

    with st.sidebar:
        render_sidebar_summary()
        st.markdown("---")
        if st.button("Tout Réinitialiser"):
            for k in st.session_state.keys(): del st.session_state[k]
            st.rerun()

    if not st.session_state.simulation_started:
        with st.expander("Configuration", expanded=True):
            presets = {"Douleur thoracique": "Homme 58 ans, fumeur. Douleur poitrine...", "Crise d'asthme": "Femme 30 ans..."}
            sel = st.selectbox("Cas", ["-- Personnalisé --"] + list(presets.keys()))
            txt = presets[sel] if sel != "-- Personnalisé --" else ""
            persona = st.text_area("Patient", value=st.session_state.patient_persona or txt)
            st.session_state.patient_persona = persona
            if st.button("Démarrer", type="primary", disabled=not persona):
                st.session_state.simulation_started = True
                st.rerun()
        return

    col_chat, col_json = st.columns([3, 2])
    with col_chat:
        suggs = st.session_state.suggested_questions or generate_question_suggestions()
        st.session_state.suggested_questions = suggs
        cols = st.columns(len(suggs))
        for i, s in enumerate(suggs):
            if cols[i].button(s, key=f"s_{i}"):
                st.session_state.pending_message = s
                st.rerun()
        
        with st.container(height=400, border=True):
            for m in st.session_state.simulation_messages:
                st.chat_message(m["role"], avatar="🧑‍⚕️" if m["role"]=="user" else "🤒").write(m["content"])

        if msg := st.chat_input("Votre question..."):
            process_nurse_message(msg)
            st.rerun()
            
        if st.session_state.pending_message:
            process_nurse_message(st.session_state.pending_message)
            st.session_state.pending_message = None
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        render_agent_reasoning()

    with col_json:
        render_json_panel()
        st.markdown("---")
        data = st.session_state.get("extracted_data", {})
        agent_res = st.session_state.get("latest_agent_result", {})
        ml_completion = calculate_ml_completion(data)
        is_emergency = agent_res.get("criticity") == "ROUGE"
        
        if ml_completion >= 100 or is_emergency:
            if st.button("🏥 VALIDER LE TRIAGE", type="primary", use_container_width=True):
                if agent_res:
                    # Mapping niveau de gravité vers niveau FRENCH et délais
                    gravity = agent_res.get("criticity", "GRIS")
                    french_mapping = {
                        "ROUGE": ("Tri 1 / Tri 2", "Immédiat / < 20 min", "SAUV / Déchocage"),
                        "JAUNE": ("Tri 3", "< 60 min", "Box Urgence"),
                        "VERT": ("Tri 4", "< 120 min", "Zone de consultation"),
                        "GRIS": ("Tri 5", "< 240 min", "Salle d'attente")
                    }
                    french_level, delai, orientation = french_mapping.get(gravity, ("Tri 5", "À évaluer", "À déterminer"))

                    # Calcul du score de confiance
                    base_confidence = 0.75
                    if ml_completion >= 100:
                        base_confidence += 0.10  # Bonus dossier complet
                    if is_emergency:
                        base_confidence = 0.95  # Red flag = haute confiance
                    confidence = min(base_confidence, 0.99)

                    # Construction de la justification
                    protocol_alert = agent_res.get("protocol_alert", "")
                    justification = protocol_alert if protocol_alert else f"Triage {gravity} basé sur l'analyse des données cliniques selon le protocole FRENCH."

                    # Recommandations basées sur le niveau
                    recommendations_map = {
                        "ROUGE": ["Prise en charge immédiate", "Monitoring continu", "Alerte médecin senior"],
                        "JAUNE": ["Surveillance rapprochée", "Réévaluation dans 30 min", "Bilan complémentaire"],
                        "VERT": ["Consultation standard", "Réévaluation si aggravation"],
                        "GRIS": ["Prise en charge différée possible", "Orientation médecine de ville si besoin"]
                    }

                    final = {
                        "gravity_level": gravity,
                        "french_triage_level": french_level,
                        "confidence_score": confidence,
                        "delai_prise_en_charge": delai,
                        "orientation": orientation,
                        "justification": justification,
                        "red_flags": [protocol_alert] if protocol_alert else agent_res.get("missing_info", [])[:3],
                        "recommendations": recommendations_map.get(gravity, [])
                    }

                    acc = st.session_state['current_interactive_session_metrics']
                    pred_id = save_triage_to_history(final, data, acc if acc['nb_calls'] > 0 else None)
                    final['prediction_id'] = pred_id
                    st.session_state.final_triage_result = final
                    st.session_state.triage_launched = True
                    st.rerun()
        else:
            st.button(f"📋 Complétez le dossier ({int(ml_completion)}%)", disabled=True, use_container_width=True)

if __name__ == "__main__":
    main()