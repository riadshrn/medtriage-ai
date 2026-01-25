"""
Mode Simulation : Cas prédéfinis pour démontrer le système
Ce mode permet de tester le système dans des conditions contrôlées
"""

import streamlit as st
import time
import requests
import os
import json
from typing import Dict, Any
# On garde uniquement les modèles de données ("Data Classes") qui sont légers
from src.models.triage_result import GravityLevel, TriageResult
# On supprime TriageAgent, Patient, ConstantesVitales qui ne servent plus ici

# Cas prédéfinis couvrant tous les niveaux de gravité
PREDEFINED_CASES = {
    "🔴 ROUGE - Arrêt Cardiaque": {
        "age": 65,
        "sexe": "M",
        "motif": "Douleur thoracique intense, perte de conscience",
        "constantes": {
            "frequence_cardiaque": 180,
            "frequence_respiratoire": 8,
            "saturation_oxygene": 75,
            "pression_systolique": 70,
            "pression_diastolique": 40,
            "temperature": 36.5,
            "echelle_douleur": 6
        },
        "description": "Patient de 65 ans présentant une douleur thoracique écrasante irradiant dans le bras gauche, sudation profuse, pâleur extrême. Perte de conscience imminente.",
        "expected_level": GravityLevel.ROUGE
    },
    "🔴 ROUGE - Traumatisme Crânien Sévère": {
        "age": 28,
        "sexe": "M",
        "motif": "Accident de moto, traumatisme crânien",
        "constantes": {
            "frequence_cardiaque": 125,
            "frequence_respiratoire": 28,
            "saturation_oxygene": 88,
            "pression_systolique": 90,
            "pression_diastolique": 55,
            "temperature": 37.2,
            "echelle_douleur": 8
        },
        "description": "Motard victime d'accident à haute vitesse, casque fissuré. Patient confus, vomissements, pupilles inégales. Suspicion d'hémorragie intracrânienne.",
        "expected_level": GravityLevel.ROUGE
    },
    "🟠 ORANGE - Fracture Ouverte": {
        "age": 42,
        "sexe": "M",
        "motif": "Chute, fracture ouverte jambe droite",
        "constantes": {
            "frequence_cardiaque": 110,
            "frequence_respiratoire": 22,
            "saturation_oxygene": 95,
            "pression_systolique": 115,
            "pression_diastolique": 70,
            "temperature": 37.0,
            "echelle_douleur": 8
        },
        "description": "Chute d'échelle (3m). Fracture ouverte tibia-péroné visible, saignement modéré, douleur intense (8/10). Patient conscient mais en état de choc.",
        "expected_level": GravityLevel.JAUNE
    },
    "🟠 ORANGE - Crise d'Asthme Sévère": {
        "age": 35,
        "sexe": "F",
        "motif": "Crise d'asthme, dyspnée importante",
        "constantes": {
            "frequence_cardiaque": 118,
            "frequence_respiratoire": 32,
            "saturation_oxygene": 89,
            "pression_systolique": 130,
            "pression_diastolique": 85,
            "temperature": 37.1,
            "echelle_douleur": 8
        },
        "description": "Patient asthmatique connu, crise déclenchée par allergène. Respiration sifflante audible, tirage intercostal, anxiété majeure. Ventoline inefficace.",
        "expected_level": GravityLevel.JAUNE
    },
    "🟡 JAUNE - Entorse Cheville": {
        "age": 25,
        "sexe": "M",
        "motif": "Entorse cheville gauche au sport",
        "constantes": {
            "frequence_cardiaque": 85,
            "frequence_respiratoire": 16,
            "saturation_oxygene": 98,
            "pression_systolique": 125,
            "pression_diastolique": 75,
            "temperature": 37.0,
            "echelle_douleur": 8
        },
        "description": "Sportif amateur, entorse lors d'un match de basket. Cheville gonflée, ecchymose, douleur à la mobilisation. Pas de déformation.",
        "expected_level": GravityLevel.JAUNE
    },
    "🟡 JAUNE - Gastro-Entérite": {
        "age": 19,
        "sexe": "F",
        "motif": "Vomissements et diarrhée depuis 24h",
        "constantes": {
            "frequence_cardiaque": 95,
            "frequence_respiratoire": 18,
            "saturation_oxygene": 98,
            "pression_systolique": 110,
            "pression_diastolique": 70,
            "temperature": 38.2,
            "echelle_douleur": 8
        },
        "description": "Étudiant présentant une gastro-entérite aiguë. Nausées, vomissements répétés, diarrhée liquide. Légère déshydratation, faiblesse générale.",
        "expected_level": GravityLevel.JAUNE
    },
    "🟢 VERT - Plaie Superficielle": {
        "age": 30,
        "sexe": "F",
        "motif": "Coupure main droite en cuisinant",
        "constantes": {
            "frequence_cardiaque": 72,
            "frequence_respiratoire": 14,
            "saturation_oxygene": 99,
            "pression_systolique": 120,
            "pression_diastolique": 75,
            "temperature": 36.8,
            "echelle_douleur": 8
        },
        "description": "Coupure nette au couteau (2cm) sur la paume de la main. Saignement mineur contrôlé par compression. Pas de lésion tendineuse apparente.",
        "expected_level": GravityLevel.VERT
    },
    "⚪ GRIS - Consultation Mineure": {
        "age": 18,
        "sexe": "M",
        "motif": "Petite écorchure au genou",
        "constantes": {
            "frequence_cardiaque": 68,
            "frequence_respiratoire": 14,
            "saturation_oxygene": 99,
            "pression_systolique": 115,
            "pression_diastolique": 72,
            "temperature": 36.6,
            "echelle_douleur": 8
        },
        "description": "Jeune patient avec écorchure superficielle suite à une chute en vélo. Plaie nettoyée, pas de corps étranger. Demande un avis médical par précaution.",
        "expected_level": GravityLevel.GRIS
    },
    "⚠️ EDGE CASE - Constantes Contradictoires": {
        "age": 55,
        "sexe": "M",
        "motif": "Malaise général",
        "constantes": {
            "frequence_cardiaque": 45,  # Bradycardie
            "frequence_respiratoire": 25,  # Tachypnée
            "saturation_oxygene": 92,  # Légère hypoxie
            "pression_systolique": 180,  # Hypertension
            "pression_diastolique": 110,
            "temperature": 39.5,  # Fièvre élevée
            "echelle_douleur": 14  # Légère altération
        },
        "description": "Patient aux constantes contradictoires : bradycardie + tachypnée + hypertension + fièvre. Tester la capacité du système à gérer des cas complexes.",
        "expected_level": GravityLevel.JAUNE  # Attendu car anomalies multiples
    },
    "⚠️ EDGE CASE - Patient Anxieux": {
        "age": 22,
        "sexe": "F",
        "motif": "Palpitations et sensation de mort imminente",
        "constantes": {
            "frequence_cardiaque": 115,  # Tachycardie de stress
            "frequence_respiratoire": 28,  # Hyperventilation
            "saturation_oxygene": 99,  # Paradoxalement normale
            "pression_systolique": 135,
            "pression_diastolique": 88,
            "temperature": 36.9,
            "echelle_douleur": 8
        },
        "description": "Possible crise de panique : tous les symptômes d'urgence cardiaque mais constantes physiologiques correctes. Tester si le système sur-triage ou identifie correctement.",
        "expected_level": GravityLevel.JAUNE  # Surveillance nécessaire même si probablement anxiété
    }
}


def render_simulation_mode():
    """Rendu du mode simulation avec cas prédéfinis"""

    st.header("🎬 Mode Simulation - Cas Prédéfinis")
    st.markdown("""
    Ce mode présente des **cas cliniques réalistes** pour démontrer le fonctionnement du système
    dans des conditions contrôlées. Chaque cas couvre un niveau de gravité différent.
    """)

    # Sélection du cas
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_case = st.selectbox(
            "Sélectionnez un cas clinique",
            options=list(PREDEFINED_CASES.keys()),
            index=0
        )

    with col2:
        use_rag = st.checkbox("Activer RAG (justifications enrichies)", value=True)
        show_metrics = st.checkbox("Afficher les métriques détaillées", value=True)

    case_data = PREDEFINED_CASES[selected_case]

    # Affichage du cas
    st.markdown("---")
    st.subheader("📋 Informations du Patient")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Âge", f"{case_data['age']} ans")
    with col2:
        st.metric("Motif", case_data['motif'])
    with col3:
        expected_emoji = {
            GravityLevel.ROUGE: "🔴",
            GravityLevel.JAUNE: "🟠",
            GravityLevel.JAUNE: "🟡",
            GravityLevel.VERT: "🟢",
            GravityLevel.GRIS: "⚪"
        }
        st.metric("Gravité Attendue", f"{expected_emoji.get(case_data['expected_level'], '❓')} {case_data['expected_level'].value}")

    # Description clinique
    st.markdown("### 📝 Description Clinique")
    st.info(case_data['description'])

    # Constantes vitales
    st.markdown("### 🩺 Constantes Vitales")
    const_col1, const_col2, const_col3, const_col4 = st.columns(4)

    constantes = case_data['constantes']
    with const_col1:
        st.metric("FC", f"{constantes['frequence_cardiaque']} bpm")
        st.metric("FR", f"{constantes['frequence_respiratoire']} /min")
    with const_col2:
        st.metric("SpO2", f"{constantes['saturation_oxygene']}%")
        st.metric("Temp", f"{constantes['temperature']}°C")
    with const_col3:
        st.metric("TAS", f"{constantes['pression_systolique']} mmHg")
        st.metric("TAD", f"{constantes['pression_diastolique']} mmHg")
    with const_col4:
        st.metric("Douleur", f"{constantes['echelle_douleur']}/10")

    # Bouton de triage
    st.markdown("---")
    if st.button("🚨 LANCER LE TRIAGE", type="primary", use_container_width=True):
        perform_triage(case_data, use_rag, show_metrics, selected_case)


def perform_triage(case_data: Dict[str, Any], use_rag: bool, show_metrics: bool, case_name: str):
    """
    Effectue le triage en appelant l'API Backend.
    Plus aucun calcul ML n'est fait ici (Client Léger).
    """
    
    # 1. Configuration de l'endpoint API
    # Dans Docker, l'hôte est "redflag-api" (nom du service), port 8000
    # Si on est en local hors docker, c'est localhost
    api_host = os.getenv("API_HOST", "redflag-api") 
    api_url = f"http://{api_host}:8000/triage/triage"  # Vérifier si le préfixe est /triage dans main.py

    with st.spinner("📡 Communication avec le cerveau central (API)..."):
        try:
            # 2. Préparation de la requête (Mapping des données)
            # L'API attend un schéma "PatientInput"
            payload = {
                "age": case_data['age'],
                "sexe": case_data['sexe'],
                "motif_consultation": case_data['motif'], # Attention: 'motif' vs 'motif_consultation'
                "constantes": case_data['constantes']
            }
            
            # Paramètre query string pour RAG
            params = {"use_rag": str(use_rag).lower()}

            # 3. Appel HTTP
            start_time = time.time()
            response = requests.post(api_url, json=payload, params=params, timeout=30)
            end_time = time.time()

            # 4. Traitement de la réponse
            if response.status_code == 200:
                api_json = response.json()
                
                # 5. Reconstruction de l'objet TriageResult pour l'affichage
                # On convertit le JSON reçu en objet Python que l'interface sait afficher
                result = TriageResult(
                    gravity_level=GravityLevel(api_json["french_triage_level"]), # Ou "predicted_level" selon ton enum
                    confidence_score=api_json["confidence_score"],
                    justification=api_json["justification"],
                    # Champs optionnels
                    ml_score=api_json.get("ml_score", 0.0),
                    latency_ml=0.0, # L'API devrait renvoyer ces métriques idéalement
                    latency_llm=0.0
                )
                
                # Si l'API renvoie le temps de traitement dans le JSON, on peut l'utiliser
                if "processing_time_ms" in api_json:
                    result.latency_ml = api_json["processing_time_ms"] / 1000

                # Affichage standard
                from src.interface.components.simulation_mode import display_triage_result
                display_triage_result(result, case_data, end_time - start_time, show_metrics, case_name)

            else:
                st.error(f"❌ Erreur API ({response.status_code})")
                st.code(response.text, language="json")

        except requests.exceptions.ConnectionError:
            st.error(f"❌ Impossible de contacter l'API à l'adresse : {api_url}")
            st.info("💡 Vérifiez que le conteneur 'redflag-api' est bien démarré.")
        except Exception as e:
            st.error(f"❌ Erreur technique : {str(e)}")
            # Pour le debug, afficher le payload envoyé
            with st.expander("Détails techniques"):
                st.write("URL:", api_url)
                st.json(payload)

def display_triage_result(result, case_data: Dict, total_time: float, show_metrics: bool, case_name: str):
    """Affiche les résultats du triage de manière visuelle"""

    st.markdown("---")
    st.header("📊 Résultat du Triage")

    # Comparaison attendu vs obtenu
    expected_level = case_data['expected_level']
    obtained_level = result.gravity_level

    is_correct = expected_level == obtained_level

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("#### Niveau Attendu")
        level_color = {
            GravityLevel.ROUGE: "rouge",
            GravityLevel.JAUNE: "orange",
            GravityLevel.JAUNE: "jaune",
            GravityLevel.VERT: "vert",
            GravityLevel.GRIS: "gris"
        }
        color = level_color.get(expected_level, "gris")
        st.markdown(
            f'<div class="triage-{color}">{expected_level.value.upper()}</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### Niveau Obtenu")
        color = level_color.get(obtained_level, "gris")
        st.markdown(
            f'<div class="triage-{color}">{obtained_level.value.upper()}</div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### Validation")
        if is_correct:
            st.success("✅ Conforme", icon="✅")
        else:
            st.warning("⚠️ Divergence", icon="⚠️")

    # Confiance et justification
    st.markdown("### 💡 Justification Clinique")
    st.markdown(f"**Confiance :** {result.confidence_score:.1%}")

    if result.confidence_score >= 0.90:
        st.success(result.justification)
    elif result.confidence_score >= 0.70:
        st.info(result.justification)
    else:
        st.warning(result.justification)

    # Métriques de performance
    if show_metrics:
        st.markdown("### ⚡ Métriques de Performance")

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.metric("Latence Totale", f"{total_time*1000:.2f} ms")
        with metric_col2:
            ml_latency = result.latency_ml * 1000 if result.latency_ml else 0
            st.metric("Latence ML", f"{ml_latency:.2f} ms")
        with metric_col3:
            if result.latency_llm:
                st.metric("Latence LLM", f"{result.latency_llm * 1000:.2f} ms")
            else:
                st.metric("Latence LLM", "N/A (non utilisé)")

    # Analyse du cas (si c'est un edge case)
    if "EDGE CASE" in case_name:
        st.markdown("### 🧪 Analyse du Cas Limite")
        st.info(f"""
        **Ce cas teste :** {case_data['description']}

        **Comportement observé :**
        - Niveau assigné : {obtained_level.value}
        - Confiance : {result.confidence_score:.1%}
        - Le système {"a correctement géré" if is_correct else "a divergé de l'attendu pour"} ce cas complexe.
        """)

    # Recommandations
    st.markdown("### 🎯 Recommandations Cliniques")
    recommendations = {
        GravityLevel.ROUGE: "🔴 **Prise en charge IMMÉDIATE** - Salle de déchocage - Équipe complète",
        GravityLevel.JAUNE: "🟠 **Prise en charge URGENTE** - Délai max 20 min - Surveillance continue",
        GravityLevel.JAUNE: "🟡 **Prise en charge PROGRAMMÉE** - Délai max 60 min - Consultation standard",
        GravityLevel.VERT: "🟢 **Prise en charge DIFFÉRÉE** - Délai max 120 min - Consultation simple",
        GravityLevel.GRIS: "⚪ **Non urgent** - Orientation possible vers médecine de ville"
    }
    st.info(recommendations.get(obtained_level, "Recommandation non disponible"))

    # Métadonnées complètes
    if show_metrics:
        with st.expander("🔍 Métadonnées Complètes"):
            st.json(result.to_dict())
