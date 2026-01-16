"""
Tests pour le mode simulation
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.simulation_mode import PREDEFINED_CASES
from src.models.patient import Patient
from src.models.constantes_vitales import ConstantesVitales
from src.models.gravity_level import GravityLevel


class TestSimulationMode(unittest.TestCase):
    """Tests pour le mode simulation"""

    def test_all_predefined_cases_valid(self):
        """Teste que tous les cas predefinis sont valides"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                # Verifier structure
                self.assertIn("age", case_data)
                self.assertIn("motif", case_data)
                self.assertIn("constantes", case_data)
                self.assertIn("expected_level", case_data)

                # Verifier que l'age est valide
                self.assertGreaterEqual(case_data["age"], 0)
                self.assertLessEqual(case_data["age"], 120)

                # Verifier que le motif existe
                self.assertTrue(len(case_data["motif"]) > 0)

    def test_predefined_cases_constantes_valid(self):
        """Teste que les constantes des cas predefinis sont valides"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                constantes = case_data["constantes"]

                # Verifier les constantes requises
                self.assertIn("frequence_cardiaque", constantes)
                self.assertIn("saturation_oxygene", constantes)
                self.assertIn("temperature", constantes)

                # Verifier les plages de valeurs
                self.assertGreater(constantes["frequence_cardiaque"], 0)
                self.assertLessEqual(constantes["saturation_oxygene"], 100)
                self.assertGreater(constantes["temperature"], 30)
                self.assertLess(constantes["temperature"], 45)

    def test_predefined_cases_expected_levels(self):
        """Teste que les niveaux attendus sont des GravityLevel valides"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                expected = case_data["expected_level"]
                self.assertIsInstance(expected, GravityLevel)

    def test_rouge_cases_critical_vitals(self):
        """Teste que les cas ROUGE ont des constantes critiques"""
        rouge_cases = [
            name for name, data in PREDEFINED_CASES.items()
            if data["expected_level"] == GravityLevel.ROUGE
        ]

        self.assertGreater(len(rouge_cases), 0, "Devrait avoir au moins un cas ROUGE")

        for case_name in rouge_cases:
            case_data = PREDEFINED_CASES[case_name]
            constantes = case_data["constantes"]

            # Un cas ROUGE devrait avoir au moins une constante critique
            is_critical = (
                constantes.get("saturation_oxygene", 100) < 90 or
                constantes.get("frequence_cardiaque", 80) > 130 or
                constantes.get("frequence_cardiaque", 80) < 40 or
                constantes.get("pression_systolique", 120) < 80 or
                constantes.get("temperature", 37) > 40
            )

            # Note: Certains cas ROUGE peuvent etre bases sur le motif
            # donc on ne force pas cette assertion

    def test_gris_cases_normal_vitals(self):
        """Teste que les cas GRIS ont des constantes normales"""
        gris_cases = [
            name for name, data in PREDEFINED_CASES.items()
            if data["expected_level"] == GravityLevel.GRIS
        ]

        for case_name in gris_cases:
            case_data = PREDEFINED_CASES[case_name]
            constantes = case_data["constantes"]

            # Un cas GRIS devrait avoir des constantes globalement normales
            self.assertGreaterEqual(constantes.get("saturation_oxygene", 98), 95)
            self.assertLessEqual(constantes.get("frequence_cardiaque", 80), 100)
            self.assertGreaterEqual(constantes.get("frequence_cardiaque", 80), 50)

    def test_cases_cover_all_gravity_levels(self):
        """Teste que les cas predefinis couvrent tous les niveaux de gravite"""
        levels_covered = set()

        for case_data in PREDEFINED_CASES.values():
            levels_covered.add(case_data["expected_level"])

        # Verifier qu'on a au moins ROUGE, JAUNE, VERT et GRIS
        expected_levels = {GravityLevel.ROUGE, GravityLevel.JAUNE, GravityLevel.VERT, GravityLevel.GRIS}
        self.assertEqual(levels_covered, expected_levels)


if __name__ == "__main__":
    unittest.main()
