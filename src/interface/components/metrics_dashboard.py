"""
Dashboard de métriques : Évaluation des performances du système
Métriques métier pertinentes pour le projet Data for Good
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.triage_result import GravityLevel
from src.agents.triage_agent import TriageAgent
from src.models.patient import Patient
from src.models.constantes_vitales import ConstantesVitales as Constantes


def render_metrics_dashboard():
    """Rendu du dashboard de métriques"""

    st.header("📊 Dashboard de Métriques")
    st.markdown("""
    Ce dashboard évalue les performances du système sur des **métriques métier pertinentes** :
    - **Accuracy** : Taux de classification correcte
    - **Latence** : Temps de réponse (critique aux urgences)
    - **Distribution** : Répartition des niveaux de triage
    - **Coût** : Utilisation des ressources (ML vs LLM)
    - **Sur-triage / Sous-triage** : Risques cliniques
    """)

    # Initialiser les données de test si nécessaire
    if 'benchmark_results' not in st.session_state:
        st.session_state.benchmark_results = None

    # Configuration du benchmark
    st.markdown("---")
    st.subheader("⚙️ Configuration du Benchmark")

    col1, col2, col3 = st.columns(3)

    with col1:
        use_rag = st.checkbox("Activer RAG", value=True)
    with col2:
        num_patients = st.slider("Nombre de patients à tester", 10, 100, 50)
    with col3:
        if st.button("🚀 Lancer le Benchmark", type="primary"):
            run_benchmark(num_patients, use_rag)

    # Afficher les résultats si disponibles
    if st.session_state.benchmark_results:
        display_benchmark_results(st.session_state.benchmark_results)
    else:
        st.info("👆 Lancez un benchmark pour voir les métriques de performance")


def run_benchmark(num_patients: int, use_rag: bool):
    """Exécute un benchmark sur N patients"""

    st.info(f"🔄 Benchmark en cours sur {num_patients} patients...")

    # Initialiser l'agent
    agent = TriageAgent(
        ml_model_path="models/trained/triage_model.json",
        ml_preprocessor_path="models/trained/preprocessor.pkl",
        vector_store_path="data/vector_store/medical_kb.pkl" if use_rag else None,
        use_rag=use_rag
    )

    # Générer des patients de test couvrant tous les niveaux
    test_patients = generate_test_patients(num_patients)

    results = {
        "total": num_patients,
        "correct": 0,
        "predictions": [],
        "latencies": [],
        "distribution": {level.value: 0 for level in GravityLevel},
        "confusion_matrix": {
            "true_positive": {level.value: 0 for level in GravityLevel},
            "false_positive": {level.value: 0 for level in GravityLevel},
            "false_negative": {level.value: 0 for level in GravityLevel}
        },
        "sur_triage": 0,
        "sous_triage": 0,
        "ml_only_count": 0,
        "llm_used_count": 0,
        "total_ml_time": 0,
        "total_llm_time": 0
    }

    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (patient, expected_level) in enumerate(test_patients):
        # Triage
        start_time = time.time()
        result = agent.triage(patient)
        latency = (time.time() - start_time) * 1000  # en ms

        # Collecter les résultats
        results["latencies"].append(latency)
        results["distribution"][result.gravity_level.value] += 1

        # Vérifier la correction
        is_correct = result.gravity_level == expected_level
        if is_correct:
            results["correct"] += 1
            results["confusion_matrix"]["true_positive"][expected_level.value] += 1
        else:
            results["confusion_matrix"]["false_positive"][result.gravity_level.value] += 1
            results["confusion_matrix"]["false_negative"][expected_level.value] += 1

            # Détecter sur-triage / sous-triage
            severity_order = [GravityLevel.GRIS, GravityLevel.VERT, GravityLevel.JAUNE, GravityLevel.JAUNE, GravityLevel.ROUGE]
            predicted_idx = severity_order.index(result.gravity_level)
            expected_idx = severity_order.index(expected_level)

            if predicted_idx > expected_idx:
                results["sur_triage"] += 1
            else:
                results["sous_triage"] += 1

        # Métriques ML/LLM
        if result.latency_ml is not None:
            results["total_ml_time"] += result.latency_ml * 1000  # Convert to ms
            results["ml_only_count"] += 1

        if result.latency_llm is not None:
            results["total_llm_time"] += result.latency_llm * 1000  # Convert to ms
            results["llm_used_count"] += 1

        # Sauvegarder la prédiction
        results["predictions"].append({
            "patient_age": patient.age,
            "motif": patient.motif_consultation,
            "expected": expected_level.value,
            "predicted": result.gravity_level.value,
            "correct": is_correct,
            "latency_ms": latency,
            "confiance": result.confidence_score
        })

        # Mise à jour de la progression
        progress = (i + 1) / num_patients
        progress_bar.progress(progress)
        status_text.text(f"Traitement : {i+1}/{num_patients} patients")

    progress_bar.empty()
    status_text.empty()

    # Calculer les métriques agrégées
    results["accuracy"] = results["correct"] / results["total"]
    results["avg_latency_ms"] = sum(results["latencies"]) / len(results["latencies"])
    results["min_latency_ms"] = min(results["latencies"])
    results["max_latency_ms"] = max(results["latencies"])
    results["avg_ml_time_ms"] = results["total_ml_time"] / results["ml_only_count"] if results["ml_only_count"] > 0 else 0
    results["avg_llm_time_ms"] = results["total_llm_time"] / results["llm_used_count"] if results["llm_used_count"] > 0 else 0
    results["sur_triage_rate"] = results["sur_triage"] / results["total"]
    results["sous_triage_rate"] = results["sous_triage"] / results["total"]
    results["timestamp"] = datetime.now().isoformat()
    results["use_rag"] = use_rag

    st.session_state.benchmark_results = results
    st.success(f"✅ Benchmark terminé ! Accuracy : {results['accuracy']:.1%}")
    st.rerun()


def generate_test_patients(num_patients: int) -> List[tuple]:
    """Génère des patients de test avec leur niveau attendu"""

    import random

    test_cases = [
        # ROUGE
        ({"age": 65, "motif": "Douleur thoracique intense, syncope", "constantes": {
            "frequence_cardiaque": 180, "frequence_respiratoire": 8, "saturation_oxygene": 75,
            "pression_systolique": 70, "pression_diastolique": 40, "temperature": 36.5, "echelle_douleur": 6
        }}, GravityLevel.ROUGE),

        ({"age": 28, "motif": "Traumatisme crânien sévère", "constantes": {
            "frequence_cardiaque": 125, "frequence_respiratoire": 28, "saturation_oxygene": 88,
            "pression_systolique": 90, "pression_diastolique": 55, "temperature": 37.2, "echelle_douleur": 8
        }}, GravityLevel.ROUGE),

        # ORANGE
        ({"age": 42, "motif": "Fracture ouverte jambe droite", "constantes": {
            "frequence_cardiaque": 110, "frequence_respiratoire": 22, "saturation_oxygene": 95,
            "pression_systolique": 115, "pression_diastolique": 70, "temperature": 37.0, "echelle_douleur": 5
        }}, GravityLevel.JAUNE),

        ({"age": 35, "motif": "Crise d'asthme sévère", "constantes": {
            "frequence_cardiaque": 118, "frequence_respiratoire": 32, "saturation_oxygene": 89,
            "pression_systolique": 130, "pression_diastolique": 85, "temperature": 37.1, "echelle_douleur": 5
        }}, GravityLevel.JAUNE),

        # JAUNE
        ({"age": 25, "motif": "Entorse cheville gauche", "constantes": {
            "frequence_cardiaque": 85, "frequence_respiratoire": 16, "saturation_oxygene": 98,
            "pression_systolique": 125, "pression_diastolique": 75, "temperature": 37.0, "echelle_douleur": 5
        }}, GravityLevel.JAUNE),

        ({"age": 19, "motif": "Gastro-entérite avec déshydratation", "constantes": {
            "frequence_cardiaque": 95, "frequence_respiratoire": 18, "saturation_oxygene": 98,
            "pression_systolique": 110, "pression_diastolique": 70, "temperature": 38.2, "echelle_douleur": 5
        }}, GravityLevel.JAUNE),

        # VERT
        ({"age": 30, "motif": "Coupure main droite superficielle", "constantes": {
            "frequence_cardiaque": 72, "frequence_respiratoire": 14, "saturation_oxygene": 99,
            "pression_systolique": 120, "pression_diastolique": 75, "temperature": 36.8, "echelle_douleur": 5
        }}, GravityLevel.VERT),

        # GRIS
        ({"age": 18, "motif": "Petite écorchure au genou", "constantes": {
            "frequence_cardiaque": 68, "frequence_respiratoire": 14, "saturation_oxygene": 99,
            "pression_systolique": 115, "pression_diastolique": 72, "temperature": 36.6, "echelle_douleur": 5
        }}, GravityLevel.GRIS),
    ]

    # Dupliquer et varier légèrement pour atteindre num_patients
    patients = []
    for _ in range(num_patients):
        base_case, expected_level = random.choice(test_cases)

        # Varier légèrement l'âge
        varied_case = base_case.copy()
        varied_case["age"] = max(1, base_case["age"] + random.randint(-5, 5))

        # Créer le patient
        patient = Patient(
            age=varied_case["age"],
            sexe=random.choice(["M", "F"]),
            motif_consultation=varied_case["motif"],
            constantes=Constantes(**varied_case["constantes"])
        )

        patients.append((patient, expected_level))

    return patients


def display_benchmark_results(results: Dict):
    """Affiche les résultats du benchmark"""

    st.markdown("---")
    st.subheader("📈 Résultats du Benchmark")

    # Métriques principales
    st.markdown("### 🎯 Métriques Principales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        accuracy = results["accuracy"]
        color = "normal" if accuracy >= 0.90 else "inverse"
        st.metric(
            "Accuracy Globale",
            f"{accuracy:.1%}",
            delta=f"{'🟢' if accuracy >= 0.90 else '🔴'} {'Excellent' if accuracy >= 0.90 else 'À améliorer'}"
        )

    with col2:
        avg_latency = results["avg_latency_ms"]
        st.metric(
            "Latence Moyenne",
            f"{avg_latency:.2f} ms",
            delta=f"{'🟢' if avg_latency < 100 else '🔴'} {'Rapide' if avg_latency < 100 else 'Lent'}"
        )

    with col3:
        sur_triage_rate = results["sur_triage_rate"]
        st.metric(
            "Taux de Sur-Triage",
            f"{sur_triage_rate:.1%}",
            delta="⚠️ Ressources gaspillées" if sur_triage_rate > 0.1 else "✅ Acceptable"
        )

    with col4:
        sous_triage_rate = results["sous_triage_rate"]
        st.metric(
            "Taux de Sous-Triage",
            f"{sous_triage_rate:.1%}",
            delta="🔴 CRITIQUE" if sous_triage_rate > 0.05 else "✅ Sûr"
        )

    # Distribution des niveaux
    st.markdown("### 📊 Distribution des Niveaux de Triage")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Prédictions du Système**")
        distribution = results["distribution"]
        for level, count in distribution.items():
            percentage = (count / results["total"]) * 100
            emoji = {"rouge": "🔴", "orange": "🟠", "jaune": "🟡", "vert": "🟢", "gris": "⚪"}
            st.progress(percentage / 100, text=f"{emoji.get(level, '❓')} {level.upper()} : {count} patients ({percentage:.1f}%)")

    with col2:
        st.markdown("**Répartition Typique aux Urgences**")
        st.info("""
        Distribution réelle observée aux urgences :
        - 🔴 ROUGE : ~5-10%
        - 🟠 ORANGE : ~15-20%
        - 🟡 JAUNE : ~30-40%
        - 🟢 VERT : ~25-35%
        - ⚪ GRIS : ~5-10%

        Votre système devrait suivre approximativement cette distribution.
        """)

    # Latences
    st.markdown("### ⚡ Analyse des Latences")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Latence Minimale", f"{results['min_latency_ms']:.2f} ms")
    with col2:
        st.metric("Latence Moyenne", f"{results['avg_latency_ms']:.2f} ms")
    with col3:
        st.metric("Latence Maximale", f"{results['max_latency_ms']:.2f} ms")

    # Breakdown ML vs LLM
    st.markdown("### 🔀 Utilisation ML vs LLM")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Machine Learning (XGBoost)**")
        st.metric("Utilisations", results["ml_only_count"])
        st.metric("Latence Moyenne ML", f"{results['avg_ml_time_ms']:.2f} ms")
        st.info("Le ML est utilisé pour TOUS les cas (décision principale)")

    with col2:
        st.markdown("**LLM + RAG**")
        st.metric("Utilisations", results["llm_used_count"])
        if results["llm_used_count"] > 0:
            st.metric("Latence Moyenne LLM", f"{results['avg_llm_time_ms']:.2f} ms")
            st.info("Le LLM est utilisé pour enrichir les justifications")
        else:
            st.warning("RAG désactivé pour ce benchmark")

    # Matrice de confusion simplifiée
    st.markdown("### 🎲 Matrice de Confusion")

    confusion = results["confusion_matrix"]

    st.markdown("**True Positives (Bien Classés)**")
    tp_data = confusion["true_positive"]
    for level, count in tp_data.items():
        if count > 0:
            emoji = {"rouge": "🔴", "orange": "🟠", "jaune": "🟡", "vert": "🟢", "gris": "⚪"}
            st.write(f"{emoji.get(level, '❓')} **{level.upper()}** : {count} patients")

    with st.expander("Voir les erreurs (False Positives / False Negatives)"):
        st.markdown("**False Positives (Sur-Triages)**")
        fp_data = confusion["false_positive"]
        for level, count in fp_data.items():
            if count > 0:
                st.write(f"- {level.upper()} : {count} faux positifs")

        st.markdown("**False Negatives (Sous-Triages)**")
        fn_data = confusion["false_negative"]
        for level, count in fn_data.items():
            if count > 0:
                st.write(f"- {level.upper()} : {count} manqués")

    # Cas individuels
    st.markdown("### 📋 Détails des Prédictions")

    with st.expander("Voir tous les cas (tableau complet)"):
        import pandas as pd
        df = pd.DataFrame(results["predictions"])
        st.dataframe(df, use_container_width=True)

    # Export des résultats
    st.markdown("### 💾 Exporter les Résultats")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Télécharger en JSON"):
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="⬇️ Cliquez pour télécharger",
                data=json_str,
                file_name=f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col2:
        if st.button("📊 Télécharger en CSV"):
            import pandas as pd
            df = pd.DataFrame(results["predictions"])
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Cliquez pour télécharger",
                data=csv,
                file_name=f"benchmark_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Analyse qualitative
    st.markdown("### 🎓 Analyse Qualitative pour le Projet")

    if results["accuracy"] >= 0.90:
        st.success("""
        ✅ **Excellente Performance**

        Le système atteint une accuracy supérieure à 90%, ce qui est **cliniquement acceptable** pour un outil d'aide à la décision.

        **Points forts :**
        - Haute précision de classification
        - Faible taux d'erreurs critiques
        """)
    else:
        st.warning("""
        ⚠️ **Performance À Améliorer**

        Le système nécessite des ajustements pour atteindre le seuil clinique de 90% d'accuracy.

        **Pistes d'amélioration :**
        - Enrichir les données d'entraînement
        - Ajuster les seuils de décision
        - Renforcer le RAG avec plus de documentation
        """)

    if results["sous_triage_rate"] > 0.05:
        st.error("""
        🔴 **ALERTE : Taux de Sous-Triage Critique**

        Le sous-triage est **dangereux** car il peut retarder la prise en charge de patients graves.

        **Action requise :** Ajuster le modèle pour être plus conservateur (préférer le sur-triage au sous-triage).
        """)
    else:
        st.success("✅ Taux de sous-triage acceptable (< 5%)")

    if results["avg_latency_ms"] < 100:
        st.success(f"""
        ⚡ **Latence Excellente** ({results['avg_latency_ms']:.2f} ms)

        Le système est suffisamment rapide pour un usage aux urgences (objectif < 100ms).
        """)
    else:
        st.info(f"""
        ℹ️ **Latence Acceptable** ({results['avg_latency_ms']:.2f} ms)

        La latence est raisonnable mais pourrait être optimisée pour un usage intensif.
        """)
