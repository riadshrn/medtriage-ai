"""
Tests pour le dashboard de metriques
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.metrics_dashboard import generate_test_patients
from src.models.patient import Patient
from src.models.gravity_level import GravityLevel


class TestMetricsDashboard(unittest.TestCase):
    """Tests pour le dashboard de metriques"""

    def test_generate_test_patients_count(self):
        """Teste le nombre de patients generes"""
        num_patients = 20
        patients = generate_test_patients(num_patients)

        self.assertEqual(len(patients), num_patients)

    def test_generate_test_patients_structure(self):
        """Teste la structure des patients generes"""
        patients = generate_test_patients(10)

        for patient, expected_level in patients:
            self.assertIsInstance(patient, Patient)
            self.assertIsInstance(expected_level, GravityLevel)

    def test_generate_test_patients_valid_ages(self):
        """Teste que les ages sont valides"""
        patients = generate_test_patients(10)

        for patient, _ in patients:
            self.assertGreaterEqual(patient.age, 0)
            self.assertLessEqual(patient.age, 120)

    def test_generate_test_patients_valid_constantes(self):
        """Teste que les constantes sont valides"""
        patients = generate_test_patients(10)

        for patient, _ in patients:
            c = patient.constantes
            self.assertGreater(c.frequence_cardiaque, 0)
            self.assertLessEqual(c.saturation_oxygene, 100)
            self.assertGreater(c.temperature, 30)
            self.assertLess(c.temperature, 45)

    def test_generate_test_patients_distribution(self):
        """Teste que la distribution des niveaux est variee"""
        patients = generate_test_patients(40)

        levels = [level for _, level in patients]
        unique_levels = set(levels)

        # On devrait avoir au moins 2 niveaux differents
        self.assertGreaterEqual(len(unique_levels), 2)


if __name__ == "__main__":
    unittest.main()
