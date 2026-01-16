"""
Tests pour les utilitaires de l'interface
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.utils import (
    validate_patient_data,
    validate_constantes_coherence,
    format_triage_result_color,
    get_emoji_for_level,
    calculate_metrics_summary
)


class TestInterfaceUtils(unittest.TestCase):
    """Tests pour les utilitaires de l'interface"""

    def test_validate_patient_data_valid(self):
        """Teste la validation de donnees valides"""
        age = 35
        motif = "Douleur thoracique"
        constantes = {
            "frequence_cardiaque": 80,
            "frequence_respiratoire": 16,
            "saturation_oxygene": 98,
            "pression_systolique": 120,
            "pression_diastolique": 80,
            "temperature": 37.0,
            "echelle_douleur": 3
        }

        is_valid, error = validate_patient_data(age, motif, constantes)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_patient_data_invalid_age(self):
        """Teste la validation avec un age invalide"""
        constantes = {
            "frequence_cardiaque": 80,
            "frequence_respiratoire": 16,
            "saturation_oxygene": 98,
            "pression_systolique": 120,
            "pression_diastolique": 80,
            "temperature": 37.0,
            "echelle_douleur": 3
        }

        # Age negatif
        is_valid, error = validate_patient_data(-5, "Motif", constantes)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

        # Age trop eleve
        is_valid, error = validate_patient_data(150, "Motif", constantes)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_patient_data_invalid_motif(self):
        """Teste la validation avec un motif invalide"""
        constantes = {
            "frequence_cardiaque": 80,
            "frequence_respiratoire": 16,
            "saturation_oxygene": 98,
            "pression_systolique": 120,
            "pression_diastolique": 80,
            "temperature": 37.0,
            "echelle_douleur": 3
        }

        # Motif vide
        is_valid, error = validate_patient_data(35, "", constantes)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

        # Motif trop long
        long_motif = "A" * 600
        is_valid, error = validate_patient_data(35, long_motif, constantes)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_patient_data_missing_constante(self):
        """Teste la validation avec une constante manquante"""
        constantes = {
            "frequence_cardiaque": 80,
            "frequence_respiratoire": 16,
            # saturation_oxygene manquante
            "pression_systolique": 120,
            "pression_diastolique": 80,
            "temperature": 37.0,
            "echelle_douleur": 3
        }

        is_valid, error = validate_patient_data(35, "Motif", constantes)
        self.assertFalse(is_valid)
        self.assertIn("saturation_oxygene", error)

    def test_format_triage_result_color(self):
        """Teste le formatage des couleurs de triage"""
        self.assertEqual(format_triage_result_color("rouge"), "triage-rouge")
        self.assertEqual(format_triage_result_color("jaune"), "triage-jaune")
        self.assertEqual(format_triage_result_color("vert"), "triage-vert")
        self.assertEqual(format_triage_result_color("gris"), "triage-gris")

        # Test case insensitive
        self.assertEqual(format_triage_result_color("ROUGE"), "triage-rouge")

        # Test niveau inconnu
        self.assertEqual(format_triage_result_color("inconnu"), "triage-gris")

    def test_get_emoji_for_level(self):
        """Teste la recuperation des emojis"""
        self.assertEqual(get_emoji_for_level("rouge"), "🔴")
        self.assertEqual(get_emoji_for_level("jaune"), "🟡")
        self.assertEqual(get_emoji_for_level("vert"), "🟢")
        self.assertEqual(get_emoji_for_level("gris"), "⚪")

        # Niveau inconnu
        self.assertEqual(get_emoji_for_level("inconnu"), "❓")

    def test_calculate_metrics_summary_empty(self):
        """Teste le calcul de metriques avec une liste vide"""
        summary = calculate_metrics_summary([])

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["accuracy"], 0.0)
        self.assertEqual(summary["avg_latency_ms"], 0.0)

    def test_calculate_metrics_summary_valid(self):
        """Teste le calcul de metriques avec des donnees valides"""
        results = [
            {"correct": True, "latency_ms": 10, "confiance": 0.95},
            {"correct": True, "latency_ms": 15, "confiance": 0.92},
            {"correct": False, "latency_ms": 20, "confiance": 0.75},
            {"correct": True, "latency_ms": 12, "confiance": 0.88},
        ]

        summary = calculate_metrics_summary(results)

        self.assertEqual(summary["total"], 4)
        self.assertAlmostEqual(summary["accuracy"], 0.75, places=2)
        self.assertAlmostEqual(summary["avg_latency_ms"], 14.25, places=2)
        self.assertAlmostEqual(summary["avg_confidence"], 0.875, places=2)
        self.assertEqual(summary["min_latency_ms"], 10)
        self.assertEqual(summary["max_latency_ms"], 20)

    def test_calculate_metrics_summary_all_correct(self):
        """Teste le calcul de metriques avec 100% d'accuracy"""
        results = [
            {"correct": True, "latency_ms": 10, "confiance": 0.95},
            {"correct": True, "latency_ms": 12, "confiance": 0.93},
        ]

        summary = calculate_metrics_summary(results)

        self.assertEqual(summary["accuracy"], 1.0)

    def test_calculate_metrics_summary_all_incorrect(self):
        """Teste le calcul de metriques avec 0% d'accuracy"""
        results = [
            {"correct": False, "latency_ms": 10, "confiance": 0.65},
            {"correct": False, "latency_ms": 12, "confiance": 0.62},
        ]

        summary = calculate_metrics_summary(results)

        self.assertEqual(summary["accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
