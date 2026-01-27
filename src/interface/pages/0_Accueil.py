import streamlit as st
import requests
import os
import sys
from pathlib import Path

# Config Paths
current_dir = Path(__file__).parent
interface_dir = current_dir.parent
sys.path.append(str(interface_dir))

from style import apply_style
from state import init_session_state

init_session_state()
apply_style()

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("Accueil")
st.markdown("### 📂 Charger une transcription")

# --- 1. GESTION DE L'ÉTAT (Initialisation) ---
if 'conversation_data' not in st.session_state:
    st.session_state['conversation_data'] = None
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
if 'last_simulation' not in st.session_state:
    st.session_state['last_simulation'] = None

# --- 2. LE WIDGET D'UPLOAD ---
# On utilise une clé unique pour éviter les conflits
uploaded_file = st.file_uploader(
    "Chargez la transcription (CSV ou TXT)", 
    type=["csv", "txt"],
    key="uploader",
    help="Format attendu : Colonne 1 = Infirmier, Colonne 2 = Patient"
)

# --- 3. LOGIQUE DE MISE À JOUR (Seulement si un fichier est présent) ---
if uploaded_file is not None:
    # On vérifie si c'est un nouveau fichier pour ne pas recharger en boucle
    # On utilise le nom du fichier comme identifiant simple
    if st.session_state.get('current_filename') != uploaded_file.name:
        with st.spinner("Lecture du fichier..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                res = requests.post(f"{API_URL}/conversation/upload", files=files)
                
                if res.status_code == 200:
                    # ✅ MISE À JOUR DE LA MÉMOIRE
                    st.session_state['conversation_data'] = res.json()
                    st.session_state['current_filename'] = uploaded_file.name
                    # On reset l'analyse précédente car le fichier a changé
                    st.session_state['analysis_done'] = False 
                    st.session_state['last_simulation'] = None
                else:
                    st.error(f"Erreur Upload : {res.text}")
            except Exception as e:
                st.error(f"Erreur technique : {e}")

# --- 4. LOGIQUE D'AFFICHAGE (Basée sur la MÉMOIRE, pas le widget) ---
# C'est ici la correction clé : on vérifie session_state, pas uploaded_file
if st.session_state['conversation_data'] is not None:
    data = st.session_state['conversation_data']
    
    # --- A. CONVERSATION (COLLAPSIBLE) ---
    is_expanded = not st.session_state['analysis_done']
    
    label_expander = f"💬 Replay : {st.session_state.get('current_filename', 'Discussion')}"
    
    with st.expander(label_expander, expanded=is_expanded):
        chat_container = st.container(height=400, border=True)
        with chat_container:
            for msg in data["messages"]:
                if msg["role"] == "infirmier":
                    with st.chat_message("user", avatar="🧑‍⚕️"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant", avatar="🤒"):
                        st.write(msg['content'])
    
    # --- B. BOUTON D'ACTION (Si analyse pas encore faite) ---
    if not st.session_state['analysis_done']:
        if st.button("✨ Extraire les infos & Analyser (LLM)", type="primary", use_container_width=True):
            with st.spinner("Le modèle lit la conversation..."):
                try:
                    resp_process = requests.post(f"{API_URL}/conversation/process", json=data)
                    
                    if resp_process.status_code == 200:
                        # ✅ SAUVEGARDE DU RÉSULTAT
                        result = resp_process.json()
                        st.session_state['last_simulation'] = result
                        st.session_state['analysis_done'] = True
                        # Ajout à l'historique pour les stats du Dashboard
                        if 'triage_history' not in st.session_state:
                            st.session_state['triage_history'] = []
                        if 'metrics_history' not in st.session_state:
                            st.session_state['metrics_history'] = []
                        gravity = result.get('triage_result', {}).get('gravity_level', 'INCONNU')
                        st.session_state['triage_history'].append(gravity)
                        # Stocker les métriques pour les totaux
                        m = result.get('metrics', {})
                        st.session_state['metrics_history'].append({
                            'cost_usd': m.get('cost_usd', 0),
                            'gwp_kgco2': m.get('gwp_kgco2', 0),
                            'energy_kwh': m.get('energy_kwh', 0)
                        })
                        st.rerun() # Recharge pour fermer l'expander
                    else:
                        st.error(f"Erreur API : {resp_process.text}")
                except Exception as e:
                    st.error(f"Erreur connexion : {e}")

    # --- C. RÉSULTATS (Si disponibles en mémoire) ---
    if st.session_state['analysis_done'] and st.session_state['last_simulation']:
        sim = st.session_state['last_simulation']
        extracted = sim['extracted_patient']
        triage = sim['triage_result']
        
        st.divider()
        
        # 1. Alerte Triage (Le plus important)
        gravite = triage['gravity_level']
        color_map = {"ROUGE": "red", "JAUNE": "orange", "VERT": "green", "GRIS": "grey"}
        color = color_map.get(gravite, "blue")
        st.markdown(f"### 🚨 Résultat Triage : :{color}[{gravite}]")
        st.info(f"**Justification :** {triage['justification']}")

        # 2. Données Brutes
        st.markdown("### 📝 Données Extraites (JSON)")
        st.json(extracted)
        
        # 3. Bouton Reset
        if st.button("🔄 Nouvelle analyse sur ce fichier"):
            st.session_state['analysis_done'] = False
            st.rerun()

else:
    # État vide
    st.info("👋 Bienvenue. Chargez une transcription pour commencer ou retrouver votre session.")