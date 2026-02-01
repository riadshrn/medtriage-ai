"""
Page Mode Interactif - Simulation de triage aux urgences.
Version Refactorisée : Full Agentic (Plus de checklist manuelle).
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
MIN_FIELDS_FOR_VALIDATION = 4  # Seuil souple pour activer le bouton de validation finale

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
    """Nettoie le dictionnaire pour l'affichage (retire les None/Empty)."""
    if not isinstance(data, dict):
        return data
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
    """
    Calcule le pourcentage de complétion basé STRICTEMENT sur les champs requis pour le ML.
    Retourne un float entre 0 et 100.
    """
    if not data:
        return 0.0
    
    # Gestion souple de la structure (au cas où l'agent encapsule dans "patient")
    root = data.get("patient", data)
    # Gestion souple des constantes (au cas où elles sont à la racine ou dans "constantes")
    constantes = root.get("constantes", root)
    
    present_count = 0
    
    for field_path in REQUIRED_FOR_ML:
        val = None
        
        if "constantes." in field_path:
            # Ex: "constantes.temperature" -> on cherche dans le sous-dict constantes
            key = field_path.split(".")[1]
            val = constantes.get(key)
        else:
            # Ex: "age" -> on cherche à la racine
            val = root.get(field_path)
            
        # Un champ est valide s'il n'est ni None, ni vide
        if val is not None and val != "" and val != []:
            present_count += 1
            
    return (present_count / len(REQUIRED_FOR_ML)) * 100

def get_triage_emoji(level: str) -> str:
    emojis = {"ROUGE": "🔴", "JAUNE": "🟡", "VERT": "🟢", "GRIS": "⚪"}
    return emojis.get(level, "⚪")

# --- APPELS API (BACKEND) ---

def call_patient_simulation(persona: str, messages: List[Dict], nurse_message: str) -> Optional[str]:
    """Génère la réponse du patient via le Backend."""
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
    """Appelle l'Agent Médical (Extraction + Triage + Raisonnement)."""
    try:
        full_text = "\n".join([
            f"{'Infirmier' if m['role'] == 'user' else 'Patient'}: {m['content']}"
            for m in messages
        ])
        
        response = requests.post(
            f"{API_URL}/simulation/agent/interact", 
            json={"text": full_text},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur Agent ({response.status_code})")
            return None
    except requests.RequestException as e:
        st.error(f"Erreur connexion Agent: {e}")
    return None

def save_triage_to_history(result: Dict, extracted_data: Dict, metrics: Dict = None) -> Optional[str]:
    """Sauvegarde le résultat final."""
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
        st.warning("Impossible de sauvegarder l'historique.")
    return None

# --- LOGIQUE MÉTIER ---

def generate_question_suggestions() -> List[str]:
    """
    Génère des suggestions basées DIRECTEMENT sur ce que l'Agent dit qu'il manque.
    C'est beaucoup plus robuste que l'ancienne checklist manuelle.
    """
    data = st.session_state.get("extracted_data", {})
    missing_list = data.get("missing_critical_info", [])
    
    # Templates simples pour transformer "temperature" en "Avez-vous de la fièvre ?"
    templates = {
        "temperature": "Avez-vous de la fièvre ou des frissons ?",
        "frequence_cardiaque": "Sentez-vous votre cœur battre vite ?",
        "douleur": "Sur une échelle de 0 à 10, à combien est votre douleur ?",
        "duree": "Depuis combien de temps ressentez-vous cela ?",
        "antecedents": "Avez-vous des antécédents médicaux ?",
        "traitement": "Prenez-vous des médicaments actuellement ?",
        "allergie": "Avez-vous des allergies ?",
        "age": "Quel âge avez-vous ?",
        "sexe": "Quel est votre sexe biologique ?",
        "pression": "Connaissez-vous votre tension habituelle ?",
        "saturation": "Avez-vous du mal à respirer ?"
    }

    suggestions = []
    
    # 1. Priorité aux manques identifiés par l'Agent
    for missing_item in missing_list:
        # On cherche un mot clé dans l'item manquant (ex: "constantes.temperature")
        for key, question in templates.items():
            if key in missing_item.lower():
                if question not in suggestions:
                    suggestions.append(question)
    
    # 2. Compléter si pas assez de suggestions
    defaults = [
        "Pouvez-vous décrire précisément ce que vous ressentez ?",
        "Depuis quand les symptômes ont-ils commencé ?",
        "Avez-vous des antécédents médicaux ?"
    ]
    for d in defaults:
        if len(suggestions) < 3 and d not in suggestions:
            suggestions.append(d)
            
    return suggestions[:3]

def process_nurse_message(message: str) -> None:
    """Orchestre la simulation : User -> Patient LLM -> Agent Analysis."""
    st.session_state.simulation_messages.append({"role": "user", "content": message})

    # 1. Réponse du Patient
    with st.spinner("Le patient réfléchit..."):
        patient_resp = call_patient_simulation(
            st.session_state.patient_persona,
            st.session_state.simulation_messages,
            message
        ) or "..." # Fallback simple
        
    st.session_state.simulation_messages.append({"role": "assistant", "content": patient_resp})

    # 2. Analyse de l'Agent
    with st.spinner("L'IA analyse..."):
        agent_result = call_agent_interact(st.session_state.simulation_messages)
        
        if agent_result and "extracted_data" in agent_result:
            # Data & Missing Info
            data = agent_result["extracted_data"]
            if "missing_info" in agent_result:
                data["missing_critical_info"] = agent_result["missing_info"]
            
            st.session_state.extracted_data = data
            st.session_state['latest_agent_result'] = agent_result
            
            # Metrics
            if "metrics" in agent_result:
                m = agent_result["metrics"]
                acc = st.session_state['current_interactive_session_metrics']
                acc['cost_usd'] += m.get('cost_usd', 0) or 0
                acc['gwp_kgco2'] += m.get('gwp_kgco2', 0) or 0
                acc['energy_kwh'] += m.get('energy_kwh', 0) or 0
                acc['nb_calls'] += 1

    # 3. Mise à jour des suggestions
    st.session_state.suggested_questions = generate_question_suggestions()

# --- COMPOSANTS UI ---

def render_agent_reasoning() -> None:
    """Affiche le raisonnement (Expander sous le chat)."""
    res = st.session_state.get("latest_agent_result")
    if not res: return

    steps = res.get("reasoning_steps", [])
    criticity = res.get("criticity", "GRIS")
    colors = {"ROUGE": "red", "JAUNE": "orange", "VERT": "green", "GRIS": "grey"}
    
    with st.expander(f"🧠 Raisonnement IA (Triage : :{colors.get(criticity, 'grey')}[{criticity}])", expanded=True):
        for step in steps:
            if "Tool Call" in step: st.caption(f"🛠️ {step}")
            elif "Finalisation" in step: st.caption("🏁 Conclusion...")
            else: st.markdown(f"- {step}")

def render_json_panel() -> None:
    """Affiche les données extraites à droite."""
    st.markdown("### 📋 Données Extraites")
    raw = st.session_state.get("extracted_data", {})
    
    if raw:
        clean = filter_empty_values(raw)
        st.json(clean)
    
        progress = calculate_ml_completion(raw)
        
        # Couleurs et messages basés sur la complétion ML
        if progress >= 100:
            color = "#28a745" # Vert
            label = "✅ Dossier complet pour le triage ML"
        else:
            color = "#dc3545" # Rouge
            label = f"❌ Données insuffisantes pour le ML ({int(progress)}%)"
        
        st.markdown(
            f"""<div style="background:#e9ecef;border-radius:5px;height:8px;margin-top:5px;">
                <div style="background:{color};width:{progress}%;height:100%;border-radius:5px;"></div>
            </div>
            <div style="text-align:right;font-size:0.8em;color:#666;margin-top:2px;">{label}</div>""", 
            unsafe_allow_html=True
        )
    else:
        st.info("En attente de données...")

def render_sidebar_summary() -> None:
    """Sidebar simplifiée : Triage temps réel + Checklist ML."""
    res = st.session_state.get("latest_agent_result")
    
    # 1. Badge Triage
    if res:
        lvl = res.get("criticity", "GRIS")
        emoji = get_triage_emoji(lvl)
        css = f"triage-{lvl.lower()}"
        
        st.sidebar.markdown("### Estimation Temps Réel")
        st.sidebar.markdown(
            f"""<div class="triage-badge {css}" style="padding:15px;text-align:center;">
                <div style="font-size:2em;">{emoji} {lvl}</div>
                <div style="font-size:0.9em;opacity:0.8;">via Protocole</div>
            </div>""", unsafe_allow_html=True
        )
        if res.get("protocol_alert"):
            st.sidebar.warning(f"⚠️ {res['protocol_alert']}")
    else:
        st.sidebar.info("Triage en attente...")

    # 2. Infos Clés (Checklist dynamique basée sur REQUIRED_FOR_ML)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Champs Requis (ML)")
    
    data = st.session_state.get("extracted_data", {})
    
    # Préparation des données pour la recherche (gestion souple des structures imbriquées)
    root = data.get("patient", data)
    const = root.get("constantes", root)
    if not isinstance(const, dict): const = {} # Sécurité

    # On itère sur la liste officielle définie en haut du fichier
    for field in sorted(REQUIRED_FOR_ML):
        val = None
        label = field
        
        # Logique de récupération de la valeur selon le chemin (ex: "constantes.temperature")
        if "constantes." in field:
            key = field.split(".")[1]
            val = const.get(key)
            label = key.replace("_", " ").capitalize()
        else:
            val = root.get(field)
            label = field.capitalize()
        
        # Raccourcis visuels pour la sidebar
        label = label.replace("Frequence", "Fréq.").replace("Pression", "Tens.").replace("Saturation", "Sat.")
        
        # Vérification présence
        is_present = val is not None and val != "" and val != []
        icon = "✅" if is_present else "⬜"
        val_display = f": **{val}**" if is_present else ""
        
        st.sidebar.markdown(f"{icon} {label}{val_display}")
    
    # 3. Affichage des manques critiques signalés par l'IA
    if "missing_critical_info" in data and data["missing_critical_info"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Manques détectés (IA) :**")
        for m in data["missing_critical_info"][:3]:
            st.sidebar.caption(f"❌ {m}")

def init_simulation_state():
    """Init des variables de session."""
    keys = {
        "simulation_messages": [],
        "patient_persona": "",
        "extracted_data": {},
        "suggested_questions": [],
        "simulation_started": False,
        "pending_message": None,
        "triage_launched": False,
        "final_triage_result": None,
        "current_interactive_session_metrics": {'cost_usd': 0, 'gwp_kgco2': 0, 'energy_kwh': 0, 'nb_calls': 0}
    }
    for k, v in keys.items():
        if k not in st.session_state: st.session_state[k] = v

# --- MAIN PAGE ---

def main():
    init_simulation_state()
    st.title("Mode Interactif")
    
    # Si Triage Final terminé -> Affichage Résultat
    if st.session_state.triage_launched and st.session_state.final_triage_result:
        res = st.session_state.final_triage_result
        lvl = res.get("gravity_level", "GRIS")
        st.markdown(f"## Résultat : {lvl} {get_triage_emoji(lvl)}")
        st.info(res.get("justification", "Pas de justification"))
        
        if st.button("Nouvelle Simulation"):
            for k in ["simulation_messages", "patient_persona", "extracted_data", "triage_launched", "final_triage_result", "simulation_started"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
        return

    # Sidebar
    with st.sidebar:
        render_sidebar_summary()
        st.markdown("---")
        if st.button("Tout Réinitialiser"):
            for k in st.session_state.keys():
                del st.session_state[k]
            st.rerun()

    # Configuration Patient (Si pas commencé)
    if not st.session_state.simulation_started:
        with st.expander("Configuration du Patient", expanded=True):
            presets = {
                "Douleur thoracique (SCA)": "Homme 58 ans, fumeur. Douleur poitrine intense irradiant bras gauche depuis 1h. Sueurs.",
                "Crise d'asthme": "Femme 30 ans, asthmatique. Difficultés respiratoires majeures depuis 30 min. Parle par mots.",
                "Traumatisme Cheville": "Jeune homme 20 ans, footballeur. Torsion cheville droite, craquement entendu. Gonflement immédiat."
            }
            sel = st.selectbox("Choisir un cas", ["-- Personnalisé --"] + list(presets.keys()))
            default_txt = presets[sel] if sel != "-- Personnalisé --" else ""
            
            persona = st.text_area("Description du patient", value=st.session_state.patient_persona or default_txt, height=100)
            st.session_state.patient_persona = persona
            
            if st.button("Démarrer", type="primary", disabled=not persona):
                st.session_state.simulation_started = True
                st.rerun()
        return

    # Interface Principale
    col_chat, col_json = st.columns([3, 2])
    
    # Colonne GAUCHE (Chat)
    with col_chat:
        suggs = st.session_state.suggested_questions
        if not suggs: 
            suggs = generate_question_suggestions()
            st.session_state.suggested_questions = suggs
            
        cols = st.columns(len(suggs))
        for idx, s in enumerate(suggs):
            if cols[idx].button(s, key=f"s_{idx}"):
                st.session_state.pending_message = s
                st.rerun()

        with st.container(height=400, border=True):
            if not st.session_state.simulation_messages:
                st.info("Posez une question pour démarrer...")
            for m in st.session_state.simulation_messages:
                avatar = "🧑‍⚕️" if m["role"] == "user" else "🤒"
                with st.chat_message(m["role"], avatar=avatar):
                    st.write(m["content"])

        if msg := st.chat_input("Votre question..."):
            process_nurse_message(msg)
            st.rerun()

        if st.session_state.pending_message:
            process_nurse_message(st.session_state.pending_message)
            st.session_state.pending_message = None
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        render_agent_reasoning()

    # Colonne DROITE (Data + Action)
    with col_json:
        render_json_panel()
        
        st.markdown("---")
        
        # --- NOUVELLE LOGIQUE DE VALIDATION ---
        data = st.session_state.get("extracted_data", {})
        agent_res = st.session_state.get("latest_agent_result", {})
        
        # 1. Calcul de la complétion ML (0-100%)
        ml_completion = calculate_ml_completion(data)
        
        # 2. Détection d'urgence ROUGE par l'agent
        is_emergency = agent_res.get("criticity") == "ROUGE"
        
        # Le bouton s'active si TOUT est là (100%) OU si c'est une urgence critique
        can_validate = ml_completion >= 100 or is_emergency
        
        if can_validate:
            if st.button("VALIDER LE TRIAGE", type="primary", use_container_width=True):
                if agent_res:
                    final = {
                        "gravity_level": agent_res.get("criticity"),
                        "french_triage_level": "Tri Agent",
                        "justification": "Triage basé sur protocole médical (RAG).",
                        "recommendations": agent_res.get("missing_info", []),
                        "red_flags": [agent_res.get("protocol_alert")] if agent_res.get("protocol_alert") else []
                    }
                    
                    acc = st.session_state['current_interactive_session_metrics']
                    save_triage_to_history(final, data, acc if acc['nb_calls'] > 0 else None)
                    
                    st.session_state.final_triage_result = final
                    st.session_state.triage_launched = True
                    st.rerun()
        else:
            # Feedback explicite sur le bouton désactivé
            missing_count = int((100 - ml_completion) / 100 * len(REQUIRED_FOR_ML))
            label = f"Complétez le dossier ({int(ml_completion)}%)"
            st.button(label, disabled=True, use_container_width=True)
if __name__ == "__main__":
    main()