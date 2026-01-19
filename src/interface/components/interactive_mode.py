"""
Mode Interactif : Chat avec un patient simulé par LLM
L'utilisateur joue le rôle de l'infirmier(e) et interroge le patient
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Optional
import time
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.patient import Patient
from src.models.constantes_vitales import ConstantesVitales as Constantes
from src.agents.triage_agent import TriageAgent
from src.models.triage_result import GravityLevel


def render_interactive_mode():
    """Rendu du mode interactif avec chat patient"""

    st.header("💬 Mode Interactif - Chat avec Patient Simulé")
    st.markdown("""
    Dans ce mode, vous jouez le rôle de l'**infirmier(e) de triage**.
    Un patient LLM-simulé se présente aux urgences. Interrogez-le pour :
    - Comprendre son motif de consultation
    - Évaluer ses symptômes
    - Prendre ses constantes vitales

    Ensuite, le système effectuera le triage automatiquement.
    """)

    # Initialisation du state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = None
    if 'patient_persona' not in st.session_state:
        st.session_state.patient_persona = None
    if 'triage_result' not in st.session_state:
        st.session_state.triage_result = None
    if 'constantes_prises' not in st.session_state:
        st.session_state.constantes_prises = False

    # Configuration du patient
    st.markdown("---")
    st.subheader("🎭 Configuration du Patient Simulé")

    col1, col2 = st.columns([2, 1])

    with col1:
        patient_type = st.selectbox(
            "Type de patient à simuler",
            options=[
                "🎲 Aléatoire (généré par LLM)",
                "🔥 Urgence Vitale (Rouge)",
                "⚡ Urgence (Orange)",
                "⏰ Peu Urgent (Jaune)",
                "✅ Non Urgent (Vert)",
                "🧪 Cas Limite (Edge Case)",
                "🎭 Simulation d'Anxiété",
                "🤥 Patient Minimisant",
                "😱 Patient Exagérant"
            ]
        )

    with col2:
        if st.button("🔄 Nouveau Patient", type="primary"):
            # Reset session
            st.session_state.chat_history = []
            st.session_state.patient_data = None
            st.session_state.patient_persona = None
            st.session_state.triage_result = None
            st.session_state.constantes_prises = False

            # Générer nouveau patient
            st.session_state.patient_persona = generate_patient_persona(patient_type)
            st.rerun()

    # Générer le patient initial si nécessaire
    if st.session_state.patient_persona is None:
        st.session_state.patient_persona = generate_patient_persona(patient_type)

    # Afficher le persona (caché du joueur en mode réaliste)
    with st.expander("👁️ Voir les Infos Patient (Mode Debug - Normalement Caché)"):
        st.json(st.session_state.patient_persona)

    # Zone de chat
    st.markdown("---")
    st.subheader("💬 Conversation avec le Patient")

    # Afficher l'historique
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_history:
            # Message initial du patient
            initial_message = get_initial_patient_message(st.session_state.patient_persona)
            st.session_state.chat_history.append({
                "role": "patient",
                "content": initial_message
            })

        for message in st.session_state.chat_history:
            if message["role"] == "nurse":
                st.chat_message("user", avatar="👨‍⚕️").write(message["content"])
            else:
                st.chat_message("assistant", avatar="🤒").write(message["content"])

    # Input infirmier
    col1, col2 = st.columns([4, 1])

    with col1:
        nurse_input = st.text_input(
            "Votre question (en tant qu'infirmier(e))",
            placeholder="Ex: Pouvez-vous me décrire vos symptômes ?",
            key="nurse_input"
        )

    with col2:
        send_button = st.button("📤 Envoyer", type="primary")

    if send_button and nurse_input:
        # Ajouter message infirmier
        st.session_state.chat_history.append({
            "role": "nurse",
            "content": nurse_input
        })

        # Générer réponse patient
        patient_response = generate_patient_response(
            st.session_state.patient_persona,
            st.session_state.chat_history,
            nurse_input
        )

        st.session_state.chat_history.append({
            "role": "patient",
            "content": patient_response
        })

        st.rerun()

    # Actions rapides
    st.markdown("#### ⚡ Actions Rapides")
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        if st.button("🩺 Prendre les Constantes", use_container_width=True):
            take_vitals(st.session_state.patient_persona)

    with action_col2:
        if st.button("📋 Résumer le Cas", use_container_width=True):
            summarize_case()

    with action_col3:
        disabled = not st.session_state.constantes_prises
        if st.button("🚨 TRIAGE FINAL", type="primary", use_container_width=True, disabled=disabled):
            perform_final_triage()

    if not st.session_state.constantes_prises:
        st.info("ℹ️ Pensez à prendre les constantes vitales avant le triage final")

    # Afficher résultat si disponible
    if st.session_state.triage_result:
        display_interactive_triage_result()


def generate_patient_persona(patient_type: str) -> Dict:
    """Génère un persona de patient selon le type sélectionné"""

    # Personas prédéfinis selon le type
    personas = {
        "🔥 Urgence Vitale (Rouge)": {
            "age": 58,
            "motif_reel": "Infarctus du myocarde en cours",
            "symptomes": [
                "Douleur thoracique intense (écrasement)",
                "Irradiation bras gauche et mâchoire",
                "Sudation profuse",
                "Nausées",
                "Sensation de mort imminente"
            ],
            "constantes": {
                "frequence_cardiaque": 125,
                "frequence_respiratoire": 26,
                "saturation_oxygene": 88,
                "pression_systolique": 85,
                "pression_diastolique": 50,
                "temperature": 36.8,
                "echelle_douleur": 14
            },
            "personnalite": "Patient très anxieux, difficulté à parler, douleur visible",
            "expected_level": GravityLevel.ROUGE
        },
        "⚡ Urgence (Orange)": {
            "age": 35,
            "motif_reel": "Fracture ouverte avant-bras droit",
            "symptomes": [
                "Douleur intense (9/10)",
                "Déformation visible",
                "Plaie avec os apparent",
                "Saignement modéré"
            ],
            "constantes": {
                "frequence_cardiaque": 105,
                "frequence_respiratoire": 20,
                "saturation_oxygene": 96,
                "pression_systolique": 120,
                "pression_diastolique": 75,
                "temperature": 37.1,
                "echelle_douleur": 7
            },
            "personnalite": "Patient coopératif mais douleur importante",
            "expected_level": GravityLevel.JAUNE
        },
        "⏰ Peu Urgent (Jaune)": {
            "age": 28,
            "motif_reel": "Gastro-entérite avec déshydratation modérée",
            "symptomes": [
                "Vomissements depuis 24h",
                "Diarrhée liquide (10 épisodes)",
                "Fatigue importante",
                "Vertiges légers"
            ],
            "constantes": {
                "frequence_cardiaque": 92,
                "frequence_respiratoire": 18,
                "saturation_oxygene": 98,
                "pression_systolique": 105,
                "pression_diastolique": 65,
                "temperature": 37.8,
                "echelle_douleur": 7
            },
            "personnalite": "Patient fatigué mais conscient et cohérent",
            "expected_level": GravityLevel.JAUNE
        },
        "✅ Non Urgent (Vert)": {
            "age": 22,
            "motif_reel": "Entorse cheville mineure",
            "symptomes": [
                "Douleur cheville gauche (4/10)",
                "Léger gonflement",
                "Peut poser le pied partiellement"
            ],
            "constantes": {
                "frequence_cardiaque": 75,
                "frequence_respiratoire": 14,
                "saturation_oxygene": 99,
                "pression_systolique": 118,
                "pression_diastolique": 72,
                "temperature": 36.7,
                "echelle_douleur": 7
            },
            "personnalite": "Patient calme, pas pressé",
            "expected_level": GravityLevel.VERT
        },
        "🎭 Simulation d'Anxiété": {
            "age": 25,
            "motif_reel": "Crise de panique (pas d'urgence médicale)",
            "symptomes": [
                "Palpitations",
                "Impression de ne pas pouvoir respirer",
                "Sensation de mort imminente",
                "Tremblements",
                "Picotements extrémités"
            ],
            "constantes": {
                "frequence_cardiaque": 118,
                "frequence_respiratoire": 28,
                "saturation_oxygene": 99,  # Normal car hyperventilation
                "pression_systolique": 140,
                "pression_diastolique": 90,
                "temperature": 36.9,
                "echelle_douleur": 7
            },
            "personnalite": "Patient très anxieux, dramatise, hyperventilation",
            "expected_level": GravityLevel.JAUNE  # Surveillance malgré anxiété
        },
        "🤥 Patient Minimisant": {
            "age": 70,
            "motif_reel": "Douleur thoracique (possible angine)",
            "symptomes": [
                "Gêne thoracique (patient dit 'petite gêne')",
                "Essoufflement à l'effort",
                "Fatigue inhabituelle depuis 2 jours"
            ],
            "constantes": {
                "frequence_cardiaque": 95,
                "frequence_respiratoire": 22,
                "saturation_oxygene": 92,
                "pression_systolique": 150,
                "pression_diastolique": 95,
                "temperature": 36.5,
                "echelle_douleur": 7
            },
            "personnalite": "Patient stoïque, minimise ses symptômes, ne veut pas déranger",
            "expected_level": GravityLevel.JAUNE  # Malgré minimisation
        },
        "😱 Patient Exagérant": {
            "age": 32,
            "motif_reel": "Rhume avec maux de tête",
            "symptomes": [
                "Mal de tête 'atroce'",
                "Nez qui coule",
                "Gorge irritée",
                "Fatigue"
            ],
            "constantes": {
                "frequence_cardiaque": 72,
                "frequence_respiratoire": 15,
                "saturation_oxygene": 99,
                "pression_systolique": 122,
                "pression_diastolique": 78,
                "temperature": 37.3,
                "echelle_douleur": 7
            },
            "personnalite": "Patient dramatique, vocabulaire catastrophique pour symptômes mineurs",
            "expected_level": GravityLevel.GRIS
        }
    }

    # Sélectionner ou générer aléatoirement
    if "Aléatoire" in patient_type:
        import random
        return random.choice(list(personas.values()))
    elif "Cas Limite" in patient_type:
        # Générer un cas avec constantes contradictoires
        return {
            "age": 45,
            "motif_reel": "Symptômes atypiques multiples",
            "symptomes": [
                "Fatigue importante",
                "Vertiges",
                "Douleur abdominale vague",
                "Palpitations intermittentes"
            ],
            "constantes": {
                "frequence_cardiaque": 50,  # Bradycardie
                "frequence_respiratoire": 24,  # Tachypnée
                "saturation_oxygene": 94,
                "pression_systolique": 165,
                "pression_diastolique": 105,
                "temperature": 38.8,
                "echelle_douleur": 14
            },
            "personnalite": "Patient confus, descriptions vagues",
            "expected_level": GravityLevel.JAUNE
        }
    else:
        # Trouver le persona correspondant
        for key, persona in personas.items():
            if key.startswith(patient_type.split()[0]):
                return persona

    # Fallback
    return personas["✅ Non Urgent (Vert)"]


def get_initial_patient_message(persona: Dict) -> str:
    """Génère le message initial du patient"""

    messages = {
        GravityLevel.ROUGE: "Aidez-moi... j'ai très mal... à la poitrine... je n'arrive plus à respirer...",
        GravityLevel.JAUNE: "Bonjour... j'ai très mal, je me suis blessé... c'est grave je pense...",
        GravityLevel.JAUNE: "Bonjour, je ne me sens vraiment pas bien depuis hier...",
        GravityLevel.VERT: "Bonjour, je me suis fait un peu mal, je voulais juste vérifier que c'est pas grave.",
        GravityLevel.GRIS: "Bonjour, je sais que c'est pas grand chose mais je préfère être sûr..."
    }

    return messages.get(
        persona.get("expected_level", GravityLevel.VERT),
        "Bonjour, je ne me sens pas bien..."
    )


def generate_patient_response(persona: Dict, chat_history: List[Dict], nurse_question: str) -> str:
    """
    Génère la réponse du patient basée sur sa personnalité et la question
    Version simplifiée sans LLM réel (simulation basée sur règles)
    """

    question_lower = nurse_question.lower()

    # Détection de l'âge
    if any(word in question_lower for word in ["âge", "age", "quel age", "ans", "vieux", "née", "naissance"]):
        age = persona.get("age", 45)
        return f"J'ai {age} ans."

    # Détection de la question sur les symptômes
    if any(word in question_lower for word in ["symptôme", "ressent", "douleur", "mal", "qu'est-ce qui", "problème", "arrivé", "passé"]):
        symptomes = persona.get("symptomes", [])
        personnalite = persona.get("personnalite", "")

        # Gérer le cas où il n'y a pas de symptômes
        if not symptomes:
            return "Je ne me sens vraiment pas bien, mais c'est difficile à décrire..."

        if "anxieux" in personnalite.lower() or "dramatique" in personnalite.lower():
            return f"Oh mon Dieu ! C'est terrible ! {symptomes[0]} ! Et aussi {symptomes[1] if len(symptomes) > 1 else 'plein d autres choses'} ! Je vais mourir ?!"
        elif "minimise" in personnalite.lower() or "stoïque" in personnalite.lower():
            return f"Oh, ce n'est rien de grave... juste {symptomes[0].lower()}... je ne voulais pas vous déranger mais ma famille a insisté..."
        elif "douleur visible" in personnalite.lower() or "intense" in personnalite.lower():
            return f"*grimace de douleur* {symptomes[0]}... et {symptomes[1] if len(symptomes) > 1 else 'ça empire'}... s'il vous plaît aidez-moi..."
        else:
            return f"J'ai {symptomes[0].lower()}, et aussi {symptomes[1].lower() if len(symptomes) > 1 else 'quelques autres symptômes'}."

    elif any(word in question_lower for word in ["depuis quand", "combien de temps", "début"]):
        durations = {
            GravityLevel.ROUGE: "Depuis environ 30 minutes... c'est arrivé brutalement...",
            GravityLevel.JAUNE: "Il y a environ 2 heures, après ma chute...",
            GravityLevel.JAUNE: "Depuis hier soir, ça a commencé progressivement...",
            GravityLevel.VERT: "Depuis ce matin, en faisant du sport...",
            GravityLevel.GRIS: "Depuis quelques jours, mais ça ne s'améliore pas vraiment..."
        }
        return durations.get(persona.get("expected_level", GravityLevel.VERT), "Depuis quelques heures...")

    elif any(word in question_lower for word in ["antécédent", "traitement", "médicament", "allergie"]):
        return "Non, pas d'antécédents particuliers... enfin, je prends juste des vitamines habituellement."

    elif any(word in question_lower for word in ["échelle", "sur 10", "intensité"]):
        levels = {
            GravityLevel.ROUGE: "10 sur 10 ! C'est insupportable !",
            GravityLevel.JAUNE: "8 ou 9 sur 10, vraiment très douloureux...",
            GravityLevel.JAUNE: "Je dirais 5 ou 6 sur 10...",
            GravityLevel.VERT: "Peut-être 3 ou 4 sur 10, supportable...",
            GravityLevel.GRIS: "2 sur 10, c'est plus gênant que douloureux..."
        }
        return levels.get(persona.get("expected_level", GravityLevel.VERT), "Environ 5 sur 10...")

    elif any(word in question_lower for word in ["constante", "tension", "température", "pouls", "mesure"]):
        return "Oui bien sûr, allez-y, vous pouvez prendre mes constantes."

    # Questions sur le sexe/genre
    elif any(word in question_lower for word in ["sexe", "homme", "femme", "monsieur", "madame", "genre"]):
        sexe = persona.get("sexe", "M")
        return "Je suis un homme." if sexe == "M" else "Je suis une femme."

    # Questions de réconfort/rassurance
    elif any(word in question_lower for word in ["mourir", "grave", "inquiet", "peur", "rassur", "calme"]):
        personnalite = persona.get("personnalite", "")
        if "anxieux" in personnalite.lower():
            return "Vous êtes sûr ? J'ai vraiment très peur... mon cœur bat trop vite..."
        else:
            return "D'accord... merci de me rassurer..."

    # Questions sur la localisation de la douleur
    elif any(word in question_lower for word in ["où", "localis", "endroit", "côté", "zone"]):
        symptomes = persona.get("symptomes", [])
        if symptomes:
            return f"C'est surtout au niveau... {symptomes[0].lower().split('(')[0]}..."
        return "C'est difficile à dire exactement où..."

    else:
        # Réponse générique mais plus naturelle
        symptomes = persona.get("symptomes", [])
        if symptomes:
            return f"Je ne sais pas trop comment répondre... mais vraiment, {symptomes[0].lower()}..."
        return "Je ne sais pas trop... je me sens juste mal..."


def take_vitals(persona: Dict):
    """Simule la prise des constantes vitales"""

    constantes = persona.get("constantes", {})

    st.session_state.chat_history.append({
        "role": "nurse",
        "content": "Je vais prendre vos constantes vitales..."
    })

    st.session_state.chat_history.append({
        "role": "patient",
        "content": "D'accord, allez-y."
    })

    # Créer un message avec les résultats
    vitals_message = f"""
**Constantes Mesurées :**
- Fréquence Cardiaque : {constantes.get('frequence_cardiaque', 'N/A')} bpm
- Fréquence Respiratoire : {constantes.get('frequence_respiratoire', 'N/A')} /min
- Saturation O2 : {constantes.get('saturation_oxygene', 'N/A')}%
- Tension : {constantes.get('tension_systolique', 'N/A')}/{constantes.get('tension_diastolique', 'N/A')} mmHg
- Température : {constantes.get('temperature', 'N/A')}°C
- Score de Glasgow : {constantes.get('glasgow', 'N/A')}/15
"""

    st.session_state.chat_history.append({
        "role": "system",
        "content": vitals_message
    })

    st.session_state.constantes_prises = True
    st.session_state.patient_data = {
        "age": persona.get("age"),
        "sexe": persona.get("sexe", "M"),
        "motif": persona.get("motif_reel"),
        "constantes": constantes
    }

    st.rerun()


def summarize_case():
    """Résume le cas du patient"""

    if not st.session_state.chat_history:
        st.warning("Aucune conversation à résumer")
        return

    # Extraire les informations clés
    symptomes_mentionnes = []
    for msg in st.session_state.chat_history:
        if msg["role"] == "patient":
            symptomes_mentionnes.append(msg["content"])

    summary = f"""
**Résumé du Cas :**
- Patient de {st.session_state.patient_persona.get('age', 'N/A')} ans
- Motif : {st.session_state.patient_persona.get('motif_reel', 'Non précisé')}
- Symptômes rapportés : {', '.join(st.session_state.patient_persona.get('symptomes', [])[:3])}
- Constantes prises : {'Oui' if st.session_state.constantes_prises else 'Non'}
"""

    st.session_state.chat_history.append({
        "role": "system",
        "content": summary
    })

    st.rerun()


def perform_final_triage():
    """Effectue le triage final"""

    if not st.session_state.patient_data:
        st.error("Veuillez prendre les constantes vitales avant le triage")
        return

    with st.spinner("🧠 Analyse du cas et triage en cours..."):
        # Créer le patient
        patient = Patient(
            age=st.session_state.patient_data["age"],
            sexe=st.session_state.patient_data["sexe"],
            motif_consultation=st.session_state.patient_data["motif"],
            constantes=Constantes(**st.session_state.patient_data["constantes"])
        )

        # Triage
        agent = TriageAgent(
            ml_model_path="models/trained/triage_model.json",
            ml_preprocessor_path="models/trained/preprocessor.pkl",
            vector_store_path="data/vector_store/medical_kb.pkl",
            use_rag=True
        )
        result = agent.triage(patient)

        st.session_state.triage_result = result

    st.rerun()


def display_interactive_triage_result():
    """Affiche le résultat du triage en mode interactif"""

    result = st.session_state.triage_result
    persona = st.session_state.patient_persona

    st.markdown("---")
    st.header("🎯 Résultat du Triage")

    # Niveau obtenu vs attendu
    col1, col2, col3 = st.columns(3)

    level_color = {
        GravityLevel.ROUGE: "rouge",
        GravityLevel.JAUNE: "orange",
        GravityLevel.JAUNE: "jaune",
        GravityLevel.VERT: "vert",
        GravityLevel.GRIS: "gris"
    }

    with col1:
        st.markdown("#### Niveau Détecté")
        color = level_color.get(result.gravity_level, "gris")
        st.markdown(
            f'<div class="triage-{color}">{result.gravity_level.value.upper()}</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### Niveau Réel")
        expected = persona.get("expected_level", GravityLevel.VERT)
        color = level_color.get(expected, "gris")
        st.markdown(
            f'<div class="triage-{color}">{expected.value.upper()}</div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### Évaluation")
        is_correct = result.gravity_level == expected
        if is_correct:
            st.success("✅ Correct", icon="✅")
        else:
            st.error("❌ Erreur", icon="❌")

    # Justification
    st.markdown("### 💡 Justification")
    st.info(result.justification)

    st.metric("Confiance", f"{result.confidence_score:.1%}")

    # Feedback pédagogique
    st.markdown("### 📚 Analyse Pédagogique")

    if is_correct:
        st.success(f"""
        ✅ **Excellent diagnostic !**

        Le système a correctement identifié le niveau de gravité comme **{result.gravity_level.value}**.

        **Points clés du cas :**
        - {persona.get('personnalite', 'N/A')}
        - Le système n'a pas été trompé par la présentation du patient
        """)
    else:
        st.warning(f"""
        ⚠️ **Divergence détectée**

        - **Triage système** : {result.gravity_level.value}
        - **Réalité clinique** : {expected.value}

        **Raisons possibles :**
        {persona.get('personnalite', 'N/A')}

        Ce cas illustre l'importance du jugement clinique humain en complément de l'IA.
        """)

    # Métadonnées
    with st.expander("🔍 Détails Techniques"):
        st.json(result.to_dict())
