"""
Mode Interactif : Chat avec un patient simulé par LLM
L'utilisateur joue le rôle de l'infirmier(e) et interroge le patient
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Optional
import time
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# --- IMPORTS OK (Modèles de données légers) ---
from src.models.patient import Patient
from src.models.constantes_vitales import ConstantesVitales as Constantes
from src.models.gravity_level import GravityLevel

# Questions suggérées par catégorie
SUGGESTED_QUESTIONS = {
    "Identité": [
        "Quel âge avez-vous ?",
        "Vous êtes un homme ou une femme ?",
    ],
    "Symptômes": [
        "Pouvez-vous me décrire vos symptômes ?",
        "Où avez-vous mal exactement ?",
        "Sur une échelle de 1 à 10, comment évaluez-vous la douleur ?",
        "Qu'est-ce qui s'est passé ?",
    ],
    "Temporalité": [
        "Depuis quand avez-vous ces symptômes ?",
        "Est-ce que ça a commencé brutalement ?",
        "Les symptômes s'aggravent-ils ?",
    ],
    "Antécédents": [
        "Avez-vous des antécédents médicaux ?",
        "Prenez-vous des médicaments ?",
        "Avez-vous des allergies connues ?",
    ],
    "Constantes": [
        "Je vais prendre vos constantes vitales.",
    ],
}


def render_interactive_mode():
    """Rendu du mode interactif avec chat patient"""

    st.header("💬 Mode Interactif - Interrogatoire Patient")

    # Configuration Mistral dans la sidebar
    with st.sidebar:
        st.markdown("### 🤖 Configuration LLM (Mistral)")
        use_mistral = st.checkbox("Utiliser Mistral API", value=True,
                                 help="Active le simulateur LLM pour des réponses plus réalistes")

        if use_mistral:
            mistral_model = st.selectbox(
                "Modèle Mistral",
                options=["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
                index=0
            )

            # Vérifier si Mistral est disponible
            simulator = PatientSimulator(model=mistral_model)
            if simulator.is_available():
                st.success("✅ Mistral API connecté")
            else:
                st.error("❌ Mistral API non disponible")
                st.caption("Vérifiez votre clé API")
                use_mistral = False

        st.session_state.use_mistral = use_mistral
        if use_mistral:
            st.session_state.mistral_model = mistral_model

    # Layout principal : Chat | JSON | Prompt LLM
    if use_mistral:
        col_chat, col_json, col_prompt = st.columns([2, 1, 1])
    else:
        col_chat, col_json = st.columns([2, 1])
        col_prompt = None

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
    if 'last_llm_response' not in st.session_state:
        st.session_state.last_llm_response = None
    if 'collected_info' not in st.session_state:
        st.session_state.collected_info = {
            "age": None,
            "sexe": None,
            "motif": None,
            "symptomes": [],
            "duree": None,
            "intensite_douleur": None,
            "antecedents": [],
            "constantes": None
        }

    with col_chat:
        # Configuration du patient
        st.markdown("### 🎭 Configuration du Patient")

        config_col1, config_col2 = st.columns([3, 1])

        with config_col1:
            patient_type = st.selectbox(
                "Type de cas",
                options=[
                    "🎲 Aléatoire",
                    "🔴 Urgence Vitale (Rouge)",
                    "🟠 Urgence (Orange)",
                    "🟡 Peu Urgent (Jaune)",
                    "🟢 Non Urgent (Vert)",
                    "😰 Patient Anxieux",
                    "🤫 Patient Minimisant",
                    "😱 Patient Exagérant"
                ],
                key="patient_type_select"
            )

        with config_col2:
            if st.button("🔄 Nouveau", type="primary", use_container_width=True):
                reset_session()
                st.session_state.patient_persona = generate_patient_persona(patient_type)
                st.rerun()

        # Générer le patient initial si nécessaire
        if st.session_state.patient_persona is None:
            st.session_state.patient_persona = generate_patient_persona(patient_type)

        # Zone de chat
        st.markdown("---")
        st.markdown("### 💬 Conversation")

        # Container de chat avec hauteur fixe
        chat_container = st.container(height=350)

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
                elif message["role"] == "patient":
                    st.chat_message("assistant", avatar="🤒").write(message["content"])
                else:  # system
                    st.info(message["content"])

        # Input de l'infirmier
        nurse_input = st.chat_input("Votre question en tant qu'infirmier(e)...")

        if nurse_input:
            process_nurse_input(nurse_input)

        # Questions suggérées
        st.markdown("### 💡 Questions Suggérées")

        # Afficher les questions par catégorie dans des colonnes
        for category, questions in SUGGESTED_QUESTIONS.items():
            with st.expander(f"**{category}**", expanded=(category == "Symptômes")):
                for q in questions:
                    if st.button(q, key=f"q_{category}_{q[:20]}", use_container_width=True):
                        process_nurse_input(q)

        # Boutons d'action
        st.markdown("---")
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("🩺 Prendre Constantes", use_container_width=True,
                        disabled=st.session_state.constantes_prises):
                take_vitals(st.session_state.patient_persona)

        with action_col2:
            can_triage = st.session_state.constantes_prises
            if st.button("🚨 TRIAGE FINAL", type="primary", use_container_width=True,
                        disabled=not can_triage):
                perform_final_triage()

        if not st.session_state.constantes_prises:
            st.caption("⚠️ Prenez les constantes avant le triage final")

    # Colonne JSON - Informations collectées en temps réel
    with col_json:
        st.markdown("### 📋 Dossier Patient")

        # Afficher le JSON des informations collectées
        display_patient_json()

        # Infos debug (cachées par défaut)
        with st.expander("🔧 Debug - Persona complet"):
            if st.session_state.patient_persona:
                st.json(st.session_state.patient_persona)

    # Colonne Prompt LLM (si Mistral activé)
    if col_prompt is not None:
        with col_prompt:
            st.markdown("### 🧠 Prompt LLM")

            if st.session_state.last_llm_response:
                llm_resp = st.session_state.last_llm_response

                # Métriques
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Tokens", llm_resp.tokens_used)
                with col_m2:
                    st.metric("Latence", f"{llm_resp.latency_ms:.0f}ms")

                st.caption(f"**Modèle:** {llm_resp.model}")

                # Prompt envoyé
                with st.expander("📤 Prompt envoyé", expanded=True):
                    st.code(llm_resp.prompt_used, language="markdown")

                # Réponse brute
                with st.expander("📥 Réponse LLM"):
                    st.info(llm_resp.content)
            else:
                st.info("Posez une question pour voir le prompt envoyé au LLM")

                # Exemple de prompt
                with st.expander("📝 Exemple de prompt"):
                    st.markdown("""
                    Le prompt contient:
                    - **Profil patient** (âge, sexe, symptômes)
                    - **Personnalité** (anxieux, stoïque, etc.)
                    - **Historique** des échanges
                    - **Règles** de comportement
                    """)

    # Afficher résultat si disponible
    if st.session_state.triage_result:
        display_interactive_triage_result()


def reset_session():
    """Réinitialise la session"""
    st.session_state.chat_history = []
    st.session_state.patient_data = None
    st.session_state.patient_persona = None
    st.session_state.triage_result = None
    st.session_state.constantes_prises = False
    st.session_state.last_llm_response = None
    st.session_state.collected_info = {
        "age": None,
        "sexe": None,
        "motif": None,
        "symptomes": [],
        "duree": None,
        "intensite_douleur": None,
        "antecedents": [],
        "constantes": None
    }


def process_nurse_input(nurse_input: str):
    """Traite l'input de l'infirmier"""
    # Ajouter message infirmier
    st.session_state.chat_history.append({
        "role": "nurse",
        "content": nurse_input
    })

    # Générer réponse patient (Mistral ou règles)
    use_mistral = st.session_state.get('use_mistral', False)
    patient_response = None

    # 1. Tentative avec Mistral (si activé)
    if use_mistral:
        try:
            # --- LAZY IMPORT CRITIQUE ---
            from src.llm.patient_simulator import PatientSimulator
            
            model = st.session_state.get('mistral_model', 'mistral-small-latest')
            simulator = PatientSimulator(model=model)

            if simulator.is_available():
                llm_response = simulator.generate_response(
                    persona=st.session_state.patient_persona,
                    nurse_question=nurse_input,
                    chat_history=st.session_state.chat_history
                )
                patient_response = llm_response.content
                st.session_state.last_llm_response = llm_response
            
        except ImportError:
            # Cas où les dépendances lourdes sont absentes (Container UI)
            pass
        except Exception as e:
            # Cas d'erreur inattendue avec le simulateur
            print(f"Erreur Simulateur: {e}")
            pass

    # 2. Fallback universel (Règles)
    # S'exécute si : Mistral désactivé OU Import échoué OU API indisponible
    if patient_response is None:
        patient_response = generate_patient_response(
            st.session_state.patient_persona,
            st.session_state.chat_history,
            nurse_input
        )
        # On nettoie la dernière réponse LLM car on est repassé en règles
        st.session_state.last_llm_response = None

    # 3. Finalisation
    st.session_state.chat_history.append({
        "role": "patient",
        "content": patient_response
    })

    # Mettre à jour les informations collectées
    update_collected_info(nurse_input, patient_response)

    st.rerun()


def display_patient_json():
    """Affiche le JSON des informations collectées"""
    info = st.session_state.collected_info

    # Calcul du pourcentage de complétion
    filled = sum(1 for v in info.values() if v is not None and v != [] and v != {})
    total = len(info)
    completion = (filled / total) * 100

    # Progress bar
    st.progress(completion / 100, text=f"Complétion: {completion:.0f}%")

    # Affichage stylisé du JSON
    st.markdown("```json")

    json_display = {
        "patient": {
            "age": info["age"] or "❓ Non renseigné",
            "sexe": info["sexe"] or "❓ Non renseigné",
        },
        "consultation": {
            "motif": info["motif"] or "❓ À déterminer",
            "symptomes": info["symptomes"] if info["symptomes"] else ["❓ À collecter"],
            "duree": info["duree"] or "❓ Non précisé",
            "douleur": info["intensite_douleur"] or "❓ Non évalué",
        },
        "antecedents": info["antecedents"] if info["antecedents"] else ["❓ À demander"],
        "constantes": info["constantes"] if info["constantes"] else "❓ Non prises"
    }

    st.code(json.dumps(json_display, indent=2, ensure_ascii=False), language="json")

    # Indicateurs visuels
    st.markdown("#### Checklist")
    checklist = [
        ("Âge", info["age"] is not None),
        ("Sexe", info["sexe"] is not None),
        ("Symptômes", len(info["symptomes"]) > 0),
        ("Durée", info["duree"] is not None),
        ("Douleur", info["intensite_douleur"] is not None),
        ("Constantes", info["constantes"] is not None),
    ]

    for item, done in checklist:
        icon = "✅" if done else "⬜"
        st.markdown(f"{icon} {item}")


def update_collected_info(question: str, response: str):
    """Met à jour les informations collectées basé sur l'échange"""
    info = st.session_state.collected_info
    persona = st.session_state.patient_persona
    q_lower = question.lower()
    r_lower = response.lower()

    # Détection de l'âge
    if any(w in q_lower for w in ["âge", "age", "ans"]):
        info["age"] = persona.get("age")

    # Détection du sexe
    if any(w in q_lower for w in ["sexe", "homme", "femme"]):
        info["sexe"] = "Homme" if persona.get("sexe", "M") == "M" else "Femme"

    # Détection des symptômes
    if any(w in q_lower for w in ["symptôme", "douleur", "mal", "ressent", "problème"]):
        symptomes = persona.get("symptomes", [])
        if symptomes and symptomes not in info["symptomes"]:
            info["symptomes"] = symptomes[:3]  # Max 3 symptômes
        info["motif"] = persona.get("motif_reel", "Non précisé")

    # Détection de la durée
    if any(w in q_lower for w in ["depuis", "quand", "combien de temps"]):
        info["duree"] = "Récent" if "minute" in r_lower or "heure" in r_lower else "Plusieurs heures/jours"

    # Détection de l'intensité
    if any(w in q_lower for w in ["échelle", "sur 10", "intensité"]):
        # Extraire le chiffre de la réponse
        for word in response.split():
            if word.isdigit():
                info["intensite_douleur"] = f"{word}/10"
                break

    # Détection des antécédents
    if any(w in q_lower for w in ["antécédent", "traitement", "médicament", "allergie"]):
        info["antecedents"] = ["Aucun antécédent significatif"]


def generate_patient_persona(patient_type: str) -> Dict:
    """Génère un persona de patient selon le type sélectionné"""

    personas = {
        "🔴 Urgence Vitale (Rouge)": {
            "age": 58,
            "sexe": "M",
            "motif_reel": "Infarctus du myocarde en cours",
            "symptomes": [
                "Douleur thoracique intense (écrasement)",
                "Irradiation bras gauche et mâchoire",
                "Sudation profuse",
                "Nausées"
            ],
            "constantes": {
                "frequence_cardiaque": 125,
                "frequence_respiratoire": 26,
                "saturation_oxygene": 88,
                "pression_systolique": 85,
                "pression_diastolique": 50,
                "temperature": 36.8,
                "echelle_douleur": 9
            },
            "personnalite": "Patient très anxieux, difficulté à parler, douleur visible",
            "expected_level": GravityLevel.ROUGE
        },
        "🟠 Urgence (Orange)": {
            "age": 35,
            "sexe": "M",
            "motif_reel": "Fracture ouverte avant-bras droit",
            "symptomes": [
                "Douleur intense au bras",
                "Déformation visible",
                "Plaie avec saignement"
            ],
            "constantes": {
                "frequence_cardiaque": 105,
                "frequence_respiratoire": 20,
                "saturation_oxygene": 96,
                "pression_systolique": 120,
                "pression_diastolique": 75,
                "temperature": 37.1,
                "echelle_douleur": 8
            },
            "personnalite": "Patient coopératif mais douleur importante",
            "expected_level": GravityLevel.JAUNE
        },
        "🟡 Peu Urgent (Jaune)": {
            "age": 28,
            "sexe": "F",
            "motif_reel": "Gastro-entérite avec déshydratation modérée",
            "symptomes": [
                "Vomissements depuis 24h",
                "Diarrhée",
                "Fatigue importante"
            ],
            "constantes": {
                "frequence_cardiaque": 92,
                "frequence_respiratoire": 18,
                "saturation_oxygene": 98,
                "pression_systolique": 105,
                "pression_diastolique": 65,
                "temperature": 37.8,
                "echelle_douleur": 4
            },
            "personnalite": "Patient fatigué mais conscient",
            "expected_level": GravityLevel.JAUNE
        },
        "🟢 Non Urgent (Vert)": {
            "age": 22,
            "sexe": "M",
            "motif_reel": "Entorse cheville mineure",
            "symptomes": [
                "Douleur cheville gauche",
                "Léger gonflement"
            ],
            "constantes": {
                "frequence_cardiaque": 75,
                "frequence_respiratoire": 14,
                "saturation_oxygene": 99,
                "pression_systolique": 118,
                "pression_diastolique": 72,
                "temperature": 36.7,
                "echelle_douleur": 3
            },
            "personnalite": "Patient calme, pas pressé",
            "expected_level": GravityLevel.VERT
        },
        "😰 Patient Anxieux": {
            "age": 25,
            "sexe": "F",
            "motif_reel": "Crise de panique",
            "symptomes": [
                "Palpitations",
                "Sensation d'étouffement",
                "Peur de mourir"
            ],
            "constantes": {
                "frequence_cardiaque": 118,
                "frequence_respiratoire": 28,
                "saturation_oxygene": 99,
                "pression_systolique": 140,
                "pression_diastolique": 90,
                "temperature": 36.9,
                "echelle_douleur": 2
            },
            "personnalite": "Patient très anxieux, dramatise, hyperventilation",
            "expected_level": GravityLevel.JAUNE
        },
        "🤫 Patient Minimisant": {
            "age": 70,
            "sexe": "M",
            "motif_reel": "Douleur thoracique (possible angine)",
            "symptomes": [
                "Gêne thoracique légère",
                "Essoufflement à l'effort",
                "Fatigue inhabituelle"
            ],
            "constantes": {
                "frequence_cardiaque": 95,
                "frequence_respiratoire": 22,
                "saturation_oxygene": 92,
                "pression_systolique": 150,
                "pression_diastolique": 95,
                "temperature": 36.5,
                "echelle_douleur": 3
            },
            "personnalite": "Patient stoïque, minimise, ne veut pas déranger",
            "expected_level": GravityLevel.JAUNE
        },
        "😱 Patient Exagérant": {
            "age": 32,
            "sexe": "F",
            "motif_reel": "Rhume avec maux de tête",
            "symptomes": [
                "Mal de tête",
                "Nez qui coule",
                "Gorge irritée"
            ],
            "constantes": {
                "frequence_cardiaque": 72,
                "frequence_respiratoire": 15,
                "saturation_oxygene": 99,
                "pression_systolique": 122,
                "pression_diastolique": 78,
                "temperature": 37.3,
                "echelle_douleur": 2
            },
            "personnalite": "Patient dramatique, vocabulaire catastrophique",
            "expected_level": GravityLevel.GRIS
        }
    }

    # Sélection
    if "Aléatoire" in patient_type:
        import random
        return random.choice(list(personas.values()))

    for key, persona in personas.items():
        if key.startswith(patient_type.split()[0]):
            return persona

    return personas["🟢 Non Urgent (Vert)"]


def get_initial_patient_message(persona: Dict) -> str:
    """Génère le message initial du patient"""

    messages = {
        GravityLevel.ROUGE: "Aidez-moi... j'ai très mal... à la poitrine... je n'arrive plus à respirer...",
        GravityLevel.JAUNE: "Bonjour... je ne me sens vraiment pas bien, j'ai besoin d'aide...",
        GravityLevel.VERT: "Bonjour, je me suis fait mal, je voulais juste vérifier.",
        GravityLevel.GRIS: "Bonjour, je sais que c'est probablement rien mais..."
    }

    return messages.get(
        persona.get("expected_level", GravityLevel.VERT),
        "Bonjour, je ne me sens pas bien..."
    )


def generate_patient_response(persona: Dict, chat_history: List[Dict], nurse_question: str) -> str:
    """Génère la réponse du patient basée sur sa personnalité"""

    question_lower = nurse_question.lower()
    personnalite = persona.get("personnalite", "").lower()
    symptomes = persona.get("symptomes", [])
    level = persona.get("expected_level", GravityLevel.VERT)

    # ===== QUESTIONS SPÉCIFIQUES D'ABORD =====

    # 1. Âge
    if any(word in question_lower for word in ["âge", "age", "quel age", "ans avez"]):
        return f"J'ai {persona.get('age', 45)} ans."

    # 2. Sexe
    if any(word in question_lower for word in ["homme ou", "femme", "monsieur", "madame", "genre"]):
        return "Je suis un homme." if persona.get("sexe", "M") == "M" else "Je suis une femme."

    # 3. Intensité douleur / Échelle (AVANT symptômes car contient "douleur")
    if any(word in question_lower for word in ["échelle", "sur 10", "1 à 10", "évaluez", "intensité", "note"]):
        pain_levels = {
            GravityLevel.ROUGE: "10 sur 10 ! C'est insupportable ! *grimace*",
            GravityLevel.JAUNE: "7 ou 8 sur 10, c'est vraiment douloureux...",
            GravityLevel.VERT: "4 sur 10, c'est supportable.",
            GravityLevel.GRIS: "2 sur 10, c'est plus gênant que douloureux."
        }
        return pain_levels.get(level, "Environ 5 sur 10...")

    # 4. Localisation (AVANT symptômes car contient "où" et "mal")
    if any(word in question_lower for word in ["où avez", "où est", "localis", "quel endroit", "exactement"]):
        if symptomes:
            # Extraire la partie avant la parenthèse
            loc = symptomes[0].split("(")[0].strip().lower()
            if "thoracique" in loc or "poitrine" in loc:
                return "Là... *montre la poitrine* ... au milieu, ça serre très fort..."
            elif "bras" in loc:
                return "Dans le bras, ça irradie jusqu'à la main..."
            else:
                return f"C'est au niveau de... {loc}..."
        return "C'est difficile à localiser précisément..."

    # 5. Durée / Temporalité
    if any(word in question_lower for word in ["depuis quand", "depuis combien", "commencé", "début", "brutalement", "soudain"]):
        durations = {
            GravityLevel.ROUGE: "Il y a environ 30 minutes... c'est arrivé d'un coup !",
            GravityLevel.JAUNE: "Ça a commencé il y a quelques heures...",
            GravityLevel.VERT: "Depuis ce matin, après le sport.",
            GravityLevel.GRIS: "Ça dure depuis plusieurs jours..."
        }
        return durations.get(level, "Depuis quelques heures...")

    # 6. Aggravation
    if any(word in question_lower for word in ["aggrav", "empire", "pire", "augment"]):
        if level == GravityLevel.ROUGE:
            return "Oui ! Ça empire de minute en minute !"
        elif level == GravityLevel.JAUNE:
            return "Oui, ça s'aggrave progressivement..."
        else:
            return "Non, c'est stable."

    # 7. Antécédents / Médicaments / Allergies
    if any(word in question_lower for word in ["antécédent", "médicament", "allergie", "traitement", "prenez"]):
        return "Non, pas d'antécédents particuliers. Je prends juste des vitamines de temps en temps."

    # 8. Constantes
    if any(word in question_lower for word in ["constante", "tension", "température", "pouls", "mesurer"]):
        return "Oui, allez-y, vous pouvez me mesurer."

    # ===== QUESTIONS GÉNÉRALES SUR LES SYMPTÔMES =====

    # 9. Description générale des symptômes (question ouverte)
    if any(word in question_lower for word in ["symptôme", "décri", "qu'est-ce qui", "que ressentez", "problème"]):
        if not symptomes:
            return "Je ne me sens vraiment pas bien, mais c'est difficile à expliquer..."

        if "anxieux" in personnalite or "dramatique" in personnalite:
            details = symptomes[0]
            if len(symptomes) > 1:
                details += f", et aussi {symptomes[1].lower()}"
            return f"Oh mon Dieu ! C'est terrible ! {details} ! *très agité*"
        elif "minimise" in personnalite or "stoïque" in personnalite:
            return f"Oh, ce n'est probablement rien... juste {symptomes[0].lower()}... je ne voulais pas déranger."
        else:
            response = f"J'ai {symptomes[0].lower()}"
            if len(symptomes) > 1:
                response += f", et aussi {symptomes[1].lower()}"
            return response + "."

    # 10. Ce qui s'est passé
    if any(word in question_lower for word in ["passé", "arrivé", "racont"]):
        if level == GravityLevel.ROUGE:
            return "J'étais en train de travailler et d'un coup... cette douleur horrible !"
        elif level == GravityLevel.JAUNE:
            return "Je suis tombé / J'ai commencé à me sentir mal progressivement..."
        else:
            return "Rien de particulier, ça a commencé doucement..."

    # 11. Réconfort
    if any(word in question_lower for word in ["mourir", "grave", "inquiet", "rassur", "calme", "va aller"]):
        if "anxieux" in personnalite:
            return "Vous êtes sûr ? J'ai vraiment très peur... mon cœur bat trop vite..."
        return "D'accord... merci de me rassurer..."

    # ===== RÉPONSE PAR DÉFAUT =====
    if symptomes:
        if "anxieux" in personnalite:
            return f"Je ne sais pas... mais j'ai vraiment mal... {symptomes[0].lower()}..."
        return f"Euh... je ne suis pas sûr de comprendre la question. Mais vraiment, {symptomes[0].lower()}..."
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

    # Message avec les résultats
    vitals_message = f"""
**📊 Constantes Mesurées :**
| Paramètre | Valeur |
|-----------|--------|
| FC | {constantes.get('frequence_cardiaque', 'N/A')} bpm |
| FR | {constantes.get('frequence_respiratoire', 'N/A')} /min |
| SpO2 | {constantes.get('saturation_oxygene', 'N/A')}% |
| TA | {constantes.get('pression_systolique', 'N/A')}/{constantes.get('pression_diastolique', 'N/A')} mmHg |
| Temp | {constantes.get('temperature', 'N/A')}°C |
| Douleur | {constantes.get('echelle_douleur', 'N/A')}/10 |
"""

    st.session_state.chat_history.append({
        "role": "system",
        "content": vitals_message
    })

    st.session_state.constantes_prises = True
    st.session_state.collected_info["constantes"] = constantes
    st.session_state.patient_data = {
        "age": persona.get("age"),
        "sexe": persona.get("sexe", "M"),
        "motif": persona.get("motif_reel"),
        "constantes": constantes
    }

    st.rerun()


def perform_final_triage():
    """Effectue le triage final"""

    if not st.session_state.patient_data:
        st.error("Veuillez prendre les constantes vitales avant le triage")
        return

    with st.spinner("🧠 Analyse et triage en cours..."):
        try:
            from src.agents.triage_agent import TriageAgent

            patient = Patient(
                age=st.session_state.patient_data["age"],
                sexe=st.session_state.patient_data["sexe"],
                motif_consultation=st.session_state.patient_data["motif"],
                constantes=Constantes(**st.session_state.patient_data["constantes"])
            )

            agent = TriageAgent(
                ml_model_path="models/trained/triage_model.json",
                ml_preprocessor_path="models/trained/preprocessor.pkl",
                vector_store_path="data/vector_store/medical_kb.pkl",
                use_rag=True
            )
            result = agent.triage(patient)
            st.session_state.triage_result = result

        except Exception as e:
            st.error(f"Erreur lors du triage: {e}")
            return

    st.rerun()


def display_interactive_triage_result():
    """Affiche le résultat du triage"""

    result = st.session_state.triage_result
    persona = st.session_state.patient_persona

    st.markdown("---")
    st.header("🎯 Résultat du Triage")

    expected = persona.get("expected_level", GravityLevel.VERT)
    obtained = result.gravity_level
    is_correct = expected == obtained

    # Affichage comparatif
    col1, col2, col3 = st.columns(3)

    level_colors = {
        GravityLevel.ROUGE: ("🔴", "#ff4444"),
        GravityLevel.JAUNE: ("🟡", "#ffbb00"),
        GravityLevel.VERT: ("🟢", "#00cc66"),
        GravityLevel.GRIS: ("⚪", "#888888")
    }

    with col1:
        emoji, color = level_colors.get(obtained, ("❓", "#666"))
        st.markdown(f"### Niveau Détecté")
        st.markdown(f"<h2 style='color:{color}'>{emoji} {obtained.value}</h2>", unsafe_allow_html=True)

    with col2:
        emoji, color = level_colors.get(expected, ("❓", "#666"))
        st.markdown(f"### Niveau Réel")
        st.markdown(f"<h2 style='color:{color}'>{emoji} {expected.value}</h2>", unsafe_allow_html=True)

    with col3:
        st.markdown("### Évaluation")
        if is_correct:
            st.success("✅ Correct !")
        else:
            st.error("❌ Divergence")

    # Justification
    st.markdown("### 💡 Justification")
    st.info(result.justification)

    # Métriques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confiance", f"{result.confidence_score:.1%}")
    with col2:
        if result.latency_ml:
            st.metric("Latence ML", f"{result.latency_ml * 1000:.0f} ms")
    with col3:
        if result.latency_llm:
            st.metric("Latence LLM", f"{result.latency_llm * 1000:.0f} ms")

    # Analyse pédagogique
    st.markdown("### 📚 Analyse")
    if is_correct:
        st.success(f"""
        **Excellent !** Le système a correctement identifié le niveau **{obtained.value}**.

        **Points clés:** {persona.get('personnalite', 'N/A')}
        """)
    else:
        st.warning(f"""
        **Divergence détectée**

        - Système: **{obtained.value}**
        - Réalité: **{expected.value}**

        **Personnalité du patient:** {persona.get('personnalite', 'N/A')}

        Ce cas illustre l'importance du jugement clinique humain.
        """)

    # Détails techniques
    with st.expander("🔍 Détails Techniques"):
        st.json(result.to_dict())
