"""
Dashboard de métriques : Évaluation des performances du système via l'API
Refactorisé pour architecture Client-Serveur (Thin Client)
"""

import streamlit as st
import requests
import json
import time
import os
import random
from typing import List, Dict
from datetime import datetime

# Imports "Safe" (Modèles de données uniquement)
from src.models.triage_result import GravityLevel
from src.models.patient import Patient
from src.models.constantes_vitales import ConstantesVitales as Constantes

def render_metrics_dashboard():
    """Rendu du dashboard de métriques"""

    st.header("📊 Dashboard de Métriques (API)")
    st.markdown("""
    Ce dashboard évalue les performances de l'API en temps réel :
    - **Accuracy** : Comparaison Prédiction API vs Vérité Terrain
    - **Latence API** : Temps de réponse total (Réseau + Calcul)
    - **Robustesse** : Capacité à gérer une charge de requêtes
    """)

    if 'benchmark_results' not in st.session_state:
        st.session_state.benchmark_results = None

    st.markdown("---")
    st.subheader("⚙️ Configuration du Benchmark")

    col1, col2, col3 = st.columns(3)

    with col1:
        use_rag = st.checkbox("Activer RAG (Côté Serveur)", value=True)
    with col2:
        num_patients = st.slider("Nombre de requêtes", 10, 50, 20)
    with col3:
        if st.button("🚀 Lancer le Benchmark API", type="primary"):
            run_api_benchmark(num_patients, use_rag)

    if st.session_state.benchmark_results:
        display_benchmark_results(st.session_state.benchmark_results)


def run_api_benchmark(num_patients: int, use_rag: bool):
    """Exécute un benchmark en appelant l'API en boucle"""

    # Configuration API
    api_host = os.getenv("API_HOST", "redflag-api")
    api_url = f"http://{api_host}:8000/triage/triage"

    st.info(f"🔄 Envoi de {num_patients} requêtes vers {api_url}...")

    # Génération des cas de test
    test_patients = generate_test_patients(num_patients)

    results = {
        "total": num_patients,
        "correct": 0,
        "errors": 0,
        "predictions": [],
        "latencies": [],
        "distribution": {level.value: 0 for level in GravityLevel},
        "confusion_matrix": {
            "true_positive": {level.value: 0 for level in GravityLevel},
            "false_positive": {level.value: 0 for level in GravityLevel},
            "false_negative": {level.value: 0 for level in GravityLevel}
        },
        "sur_triage": 0,
        "sous_triage": 0
    }

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (patient, expected_level) in enumerate(test_patients):
        # Préparation Payload
        payload = {
            "age": patient.age,
            "sexe": patient.sexe,
            "motif_consultation": patient.motif_consultation,
            "constantes": {
                "frequence_cardiaque": patient.constantes.frequence_cardiaque,
                "frequence_respiratoire": patient.constantes.frequence_respiratoire,
                "saturation_oxygene": patient.constantes.saturation_oxygene,
                "pression_systolique": patient.constantes.pression_systolique,
                "pression_diastolique": patient.constantes.pression_diastolique,
                "temperature": patient.constantes.temperature,
                "echelle_douleur": patient.constantes.echelle_douleur
            }
        }

        # Appel API
        start_time = time.time()
        try:
            response = requests.post(api_url, json=payload, params={"use_rag": str(use_rag).lower()}, timeout=10)
            latency = (time.time() - start_time) * 1000 # ms
            
            if response.status_code == 200:
                api_data = response.json()
                
                # Récupération du niveau prédit (Mapping selon format API)
                predicted_str = api_data.get("french_triage_level") or api_data.get("predicted_level")
                # Conversion string -> Enum (Gestion d'erreur si format inconnu)
                try:
                    predicted_level = GravityLevel(predicted_str)
                except ValueError:
                    # Fallback si l'API renvoie un format différent
                    predicted_level = GravityLevel.GRIS 

                # Analyse résultats
                results["latencies"].append(latency)
                results["distribution"][predicted_level.value] += 1
                
                is_correct = predicted_level == expected_level
                
                if is_correct:
                    results["correct"] += 1
                    results["confusion_matrix"]["true_positive"][expected_level.value] += 1
                else:
                    results["confusion_matrix"]["false_positive"][predicted_level.value] += 1
                    results["confusion_matrix"]["false_negative"][expected_level.value] += 1
                    
                    # Analyse Sur/Sous triage
                    severity_order = [GravityLevel.GRIS, GravityLevel.VERT, GravityLevel.JAUNE, GravityLevel.ROUGE]
                    # Note: simplified logic here for robustness
                    try:
                        p_idx = severity_order.index(predicted_level) if predicted_level in severity_order else 0
                        e_idx = severity_order.index(expected_level) if expected_level in severity_order else 0
                        
                        if p_idx > e_idx:
                            results["sur_triage"] += 1
                        elif p_idx < e_idx:
                            results["sous_triage"] += 1
                    except ValueError:
                        pass # Ignore sorting errors

                # Log
                results["predictions"].append({
                    "patient_age": patient.age,
                    "expected": expected_level.value,
                    "predicted": predicted_level.value,
                    "correct": is_correct,
                    "latency": latency
                })
            else:
                results["errors"] += 1
                
        except Exception as e:
            results["errors"] += 1
            print(f"Error benchmark: {e}")

        # UI Update
        progress = (i + 1) / num_patients
        progress_bar.progress(progress)
        status_text.text(f"Requête API : {i+1}/{num_patients}")

    progress_bar.empty()
    status_text.empty()

    # Calcul finaux
    valid_total = results["total"] - results["errors"]
    if valid_total > 0:
        results["accuracy"] = results["correct"] / valid_total
        results["avg_latency_ms"] = sum(results["latencies"]) / len(results["latencies"])
        results["min_latency_ms"] = min(results["latencies"])
        results["max_latency_ms"] = max(results["latencies"])
        results["sur_triage_rate"] = results["sur_triage"] / valid_total
        results["sous_triage_rate"] = results["sous_triage"] / valid_total
    else:
        results["accuracy"] = 0
        results["avg_latency_ms"] = 0
        results["min_latency_ms"] = 0
        results["max_latency_ms"] = 0
        results["sur_triage_rate"] = 0
        results["sous_triage_rate"] = 0

    st.session_state.benchmark_results = results
    
    if results["errors"] > 0:
        st.warning(f"⚠️ {results['errors']} erreurs de connexion API détectées.")
    
    st.rerun()

def generate_test_patients(num_patients: int) -> List[tuple]:
    """Génère des patients de test (Version Dict simplifiée pour éviter dépendances)"""
    
    # Cas de base (Template)
    test_cases = [
        ({"age": 65, "motif": "Douleur thoracique", "constantes": {"frequence_cardiaque": 180, "frequence_respiratoire": 28, "saturation_oxygene": 85, "pression_systolique": 80, "pression_diastolique": 50, "temperature": 36.5, "echelle_douleur": 8}}, GravityLevel.ROUGE),
        ({"age": 25, "motif": "Entorse cheville", "constantes": {"frequence_cardiaque": 80, "frequence_respiratoire": 16, "saturation_oxygene": 99, "pression_systolique": 120, "pression_diastolique": 80, "temperature": 37.0, "echelle_douleur": 4}}, GravityLevel.JAUNE),
        ({"age": 30, "motif": "Coupure doigt", "constantes": {"frequence_cardiaque": 70, "frequence_respiratoire": 14, "saturation_oxygene": 99, "pression_systolique": 120, "pression_diastolique": 80, "temperature": 37.0, "echelle_douleur": 2}}, GravityLevel.VERT),
    ]

    patients = []
    for _ in range(num_patients):
        base, expected = random.choice(test_cases)
        
        # Variation légère pour éviter le cache strict
        var_age = base["age"] + random.randint(-5, 5)
        
        # Création objet Patient (Léger)
        p = Patient(
            age=max(1, var_age),
            sexe=random.choice(["M", "F"]),
            motif_consultation=base["motif"],
            constantes=Constantes(**base["constantes"])
        )
        patients.append((p, expected))
        
    return patients

def display_benchmark_results(results: Dict):
    """Affichage des résultats (inchangé sauf nettoyage)"""
    st.markdown("---")
    st.subheader("📈 Résultats du Benchmark API")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Accuracy", f"{results['accuracy']:.1%}")
    with col2:
        st.metric("Latence Moyenne", f"{results['avg_latency_ms']:.0f} ms")
    with col3:
        st.metric("Requêtes Réussies", f"{results['total'] - results['errors']} / {results['total']}")

    # Matrice Confusion
    st.markdown("### 🎲 Matrice de Confusion")
    confusion = results["confusion_matrix"]
    
    # Affichage simple
    cols = st.columns(len(GravityLevel))
    for i, level in enumerate(GravityLevel):
        count = confusion["true_positive"].get(level.value, 0)
        with cols[i]:
            st.metric(f"{level.value}", count, help="Bien classés")

    # Détails
    with st.expander("Voir les détails"):
        st.json(results)