"""
Tests pour le dashboard de métriques
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.metrics_dashboard import generate_test_patients
from src.models.patient import Patient
from src.models.triage_result import GravityLevel
from src.agents.triage_agent import TriageAgent


class TestMetricsDashboard(unittest.TestCase):
    """Tests pour le dashboard de métriques"""

    def test_generate_test_patients(self):
        """Teste la génération de patients de test"""
        num_patients = 20
        patients = generate_test_patients(num_patients)

        self.assertEqual(len(patients), num_patients)

        # Vérifier structure
        for patient, expected_level in patients:
            self.assertIsInstance(patient, Patient)
            self.assertIsInstance(expected_level, GravityLevel)

    def test_generate_test_patients_variety(self):
        """Teste que les patients générés sont variés"""
        patients = generate_test_patients(50)

        ages = [patient.age for patient, _ in patients]
        motifs = [patient.motif_consultation for patient, _ in patients]
        levels = [expected_level for _, expected_level in patients]

        # Vérifier variété des âges
        unique_ages = set(ages)
        self.assertGreater(len(unique_ages), 5, "Not enough age variety")

        # Vérifier variété des motifs
        unique_motifs = set(motifs)
        self.assertGreater(len(unique_motifs), 3, "Not enough motif variety")

        # Vérifier que plusieurs niveaux sont représentés
        unique_levels = set(levels)
        self.assertGreaterEqual(len(unique_levels), 3, "Not enough level variety")

    def test_test_patients_valid_constantes(self):
        """Teste que tous les patients ont des constantes valides"""
        patients = generate_test_patients(20)

        for patient, _ in patients:
            const = patient.constantes

            # Vérifier présence
            self.assertIsNotNone(const.frequence_cardiaque)
            self.assertIsNotNone(const.frequence_respiratoire)
            self.assertIsNotNone(const.saturation_oxygene)
            self.assertIsNotNone(const.tension_systolique)
            self.assertIsNotNone(const.tension_diastolique)
            self.assertIsNotNone(const.temperature)
            self.assertIsNotNone(const.glasgow)

            # Vérifier plages
            self.assertGreaterEqual(const.frequence_cardiaque, 30)
            self.assertLessEqual(const.frequence_cardiaque, 200)

            self.assertGreaterEqual(const.saturation_oxygene, 60)
            self.assertLessEqual(const.saturation_oxygene, 100)

            self.assertGreaterEqual(const.glasgow, 3)
            self.assertLessEqual(const.glasgow, 15)

    def test_benchmark_simulation(self):
        """Teste une simulation de benchmark simplifiée"""
        # Générer quelques patients
        patients = generate_test_patients(10)
        agent = TriageAgent(use_rag=False, verbose=False)

        results = []
        for patient, expected_level in patients:
            result = agent.triage_patient(patient)
            is_correct = result.niveau_gravite == expected_level
            results.append(is_correct)

        # Vérifier qu'on a des résultats
        self.assertEqual(len(results), 10)
        self.assertTrue(any(results), "All predictions were wrong")

    def test_accuracy_calculation(self):
        """Teste le calcul de l'accuracy"""
        results = [True, True, False, True, True, False, True, True, True, False]
        accuracy = sum(results) / len(results)

        self.assertAlmostEqual(accuracy, 0.7, places=2)

    def test_latency_tracking(self):
        """Teste le tracking de latence"""
        import time

        patients = generate_test_patients(5)
        agent = TriageAgent(use_rag=False, verbose=False)

        latencies = []
        for patient, _ in patients:
            start = time.time()
            result = agent.triage_patient(patient)
            end = time.time()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        # Vérifier qu'on a bien des latences
        self.assertEqual(len(latencies), 5)

        # Vérifier que les latences sont raisonnables
        avg_latency = sum(latencies) / len(latencies)
        self.assertLess(avg_latency, 5000, "Latency too high (>5s)")
        self.assertGreater(avg_latency, 0, "Latency must be positive")

    def test_distribution_tracking(self):
        """Teste le tracking de la distribution"""
        patients = generate_test_patients(20)
        agent = TriageAgent(use_rag=False, verbose=False)

        distribution = {level.value: 0 for level in GravityLevel}

        for patient, _ in patients:
            result = agent.triage_patient(patient)
            distribution[result.niveau_gravite.value] += 1

        # Vérifier que la somme = total
        total = sum(distribution.values())
        self.assertEqual(total, 20)

        # Vérifier qu'au moins un niveau a des patients
        self.assertGreater(max(distribution.values()), 0)

    def test_sur_triage_detection(self):
        """Teste la détection du sur-triage"""
        severity_order = [
            GravityLevel.GRIS,
            GravityLevel.VERT,
            GravityLevel.JAUNE,
            GravityLevel.ORANGE,
            GravityLevel.ROUGE
        ]

        # Cas de sur-triage
        expected = GravityLevel.JAUNE
        predicted = GravityLevel.ROUGE

        expected_idx = severity_order.index(expected)
        predicted_idx = severity_order.index(predicted)

        is_sur_triage = predicted_idx > expected_idx
        self.assertTrue(is_sur_triage)

    def test_sous_triage_detection(self):
        """Teste la détection du sous-triage"""
        severity_order = [
            GravityLevel.GRIS,
            GravityLevel.VERT,
            GravityLevel.JAUNE,
            GravityLevel.ORANGE,
            GravityLevel.ROUGE
        ]

        # Cas de sous-triage
        expected = GravityLevel.ROUGE
        predicted = GravityLevel.JAUNE

        expected_idx = severity_order.index(expected)
        predicted_idx = severity_order.index(predicted)

        is_sous_triage = predicted_idx < expected_idx
        self.assertTrue(is_sous_triage)

    def test_confusion_matrix_structure(self):
        """Teste la structure de la matrice de confusion"""
        confusion_matrix = {
            "true_positive": {level.value: 0 for level in GravityLevel},
            "false_positive": {level.value: 0 for level in GravityLevel},
            "false_negative": {level.value: 0 for level in GravityLevel}
        }

        # Vérifier structure
        self.assertIn("true_positive", confusion_matrix)
        self.assertIn("false_positive", confusion_matrix)
        self.assertIn("false_negative", confusion_matrix)

        # Vérifier que tous les niveaux sont présents
        for level in GravityLevel:
            self.assertIn(level.value, confusion_matrix["true_positive"])
            self.assertIn(level.value, confusion_matrix["false_positive"])
            self.assertIn(level.value, confusion_matrix["false_negative"])

    def test_ml_vs_llm_tracking(self):
        """Teste le tracking ML vs LLM"""
        patients = generate_test_patients(5)

        # Test avec RAG désactivé
        agent_no_rag = TriageAgent(use_rag=False, verbose=False)
        ml_only_count = 0

        for patient, _ in patients:
            result = agent_no_rag.triage_patient(patient)
            if "latence_ml_ms" in result.metadata:
                ml_only_count += 1

        self.assertEqual(ml_only_count, 5, "All should use ML")

    def test_performance_metrics_completeness(self):
        """Teste que toutes les métriques de performance sont calculées"""
        # Simule un résultat de benchmark
        mock_results = {
            "total": 10,
            "correct": 8,
            "latencies": [1.5, 2.0, 1.8, 2.2, 1.9, 2.1, 1.7, 2.3, 1.6, 2.4],
            "distribution": {
                "rouge": 2,
                "orange": 3,
                "jaune": 3,
                "vert": 1,
                "gris": 1
            },
            "sur_triage": 1,
            "sous_triage": 1,
            "ml_only_count": 10,
            "total_ml_time": 15.0,
            "llm_used_count": 0,
            "total_llm_time": 0
        }

        # Calculer les métriques
        accuracy = mock_results["correct"] / mock_results["total"]
        avg_latency = sum(mock_results["latencies"]) / len(mock_results["latencies"])
        sur_triage_rate = mock_results["sur_triage"] / mock_results["total"]
        sous_triage_rate = mock_results["sous_triage"] / mock_results["total"]

        # Vérifier
        self.assertAlmostEqual(accuracy, 0.8, places=2)
        self.assertGreater(avg_latency, 0)
        self.assertLess(avg_latency, 10)
        self.assertGreaterEqual(sur_triage_rate, 0)
        self.assertGreaterEqual(sous_triage_rate, 0)

    def test_all_gravity_levels_in_test_set(self):
        """Teste que tous les niveaux de gravité sont représentés dans le jeu de test"""
        patients = generate_test_patients(100)

        levels_seen = set()
        for _, expected_level in patients:
            levels_seen.add(expected_level)

        # Vérifier qu'on a au moins 4 niveaux différents
        self.assertGreaterEqual(len(levels_seen), 4, "Not enough level diversity in test set")


if __name__ == "__main__":
    unittest.main()
