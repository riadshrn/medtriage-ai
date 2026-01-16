"""
Tests pour le mode simulation
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.simulation_mode import PREDEFINED_CASES
from src.models.patient import Patient, Constantes
from src.models.triage_result import GravityLevel
from src.agents.triage_agent import TriageAgent


class TestSimulationMode(unittest.TestCase):
    """Tests pour le mode simulation"""

    def setUp(self):
        """Setup avant chaque test"""
        self.agent = TriageAgent(use_rag=False, verbose=False)

    def test_all_predefined_cases_valid(self):
        """Teste que tous les cas prédéfinis sont valides"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                # Vérifier structure
                self.assertIn("age", case_data)
                self.assertIn("motif", case_data)
                self.assertIn("constantes", case_data)
                self.assertIn("expected_level", case_data)

                # Vérifier types
                self.assertIsInstance(case_data["age"], int)
                self.assertIsInstance(case_data["motif"], str)
                self.assertIsInstance(case_data["constantes"], dict)
                self.assertIsInstance(case_data["expected_level"], GravityLevel)

                # Vérifier constantes
                constantes = case_data["constantes"]
                required_keys = [
                    "frequence_cardiaque",
                    "frequence_respiratoire",
                    "saturation_oxygene",
                    "tension_systolique",
                    "tension_diastolique",
                    "temperature",
                    "glasgow"
                ]
                for key in required_keys:
                    self.assertIn(key, constantes, f"Missing key {key} in {case_name}")

    def test_all_gravity_levels_covered(self):
        """Teste que tous les niveaux de gravité sont représentés"""
        levels_covered = set()
        for case_data in PREDEFINED_CASES.values():
            levels_covered.add(case_data["expected_level"])

        # Vérifier que les 5 niveaux sont couverts
        self.assertEqual(len(levels_covered), 5)
        for level in GravityLevel:
            self.assertIn(level, levels_covered)

    def test_rouge_cases_triage(self):
        """Teste le triage des cas ROUGE"""
        rouge_cases = [
            name for name, data in PREDEFINED_CASES.items()
            if data["expected_level"] == GravityLevel.ROUGE
        ]

        for case_name in rouge_cases:
            with self.subTest(case=case_name):
                case_data = PREDEFINED_CASES[case_name]

                # Créer patient
                patient = Patient(
                    age=case_data["age"],
                    motif_consultation=case_data["motif"],
                    constantes=Constantes(**case_data["constantes"])
                )

                # Triage
                result = self.agent.triage_patient(patient)

                # Vérifier
                self.assertEqual(
                    result.niveau_gravite,
                    GravityLevel.ROUGE,
                    f"Failed for {case_name}: got {result.niveau_gravite.value}"
                )

    def test_orange_cases_triage(self):
        """Teste le triage des cas ORANGE"""
        orange_cases = [
            name for name, data in PREDEFINED_CASES.items()
            if data["expected_level"] == GravityLevel.ORANGE
        ]

        for case_name in orange_cases:
            with self.subTest(case=case_name):
                case_data = PREDEFINED_CASES[case_name]

                patient = Patient(
                    age=case_data["age"],
                    motif_consultation=case_data["motif"],
                    constantes=Constantes(**case_data["constantes"])
                )

                result = self.agent.triage_patient(patient)

                # ORANGE ou ROUGE acceptables (car edge cases peuvent varier)
                self.assertIn(
                    result.niveau_gravite,
                    [GravityLevel.ORANGE, GravityLevel.ROUGE],
                    f"Failed for {case_name}: got {result.niveau_gravite.value}"
                )

    def test_edge_cases_handled(self):
        """Teste que les cas limites sont gérés sans erreur"""
        edge_cases = [
            name for name in PREDEFINED_CASES.keys()
            if "EDGE CASE" in name
        ]

        self.assertGreater(len(edge_cases), 0, "No edge cases defined")

        for case_name in edge_cases:
            with self.subTest(case=case_name):
                case_data = PREDEFINED_CASES[case_name]

                patient = Patient(
                    age=case_data["age"],
                    motif_consultation=case_data["motif"],
                    constantes=Constantes(**case_data["constantes"])
                )

                # Ne doit pas planter
                try:
                    result = self.agent.triage_patient(patient)
                    self.assertIsNotNone(result)
                    self.assertIsNotNone(result.niveau_gravite)
                    self.assertIsNotNone(result.justification)
                except Exception as e:
                    self.fail(f"Edge case {case_name} raised exception: {e}")

    def test_constantes_ranges_realistic(self):
        """Teste que les constantes sont dans des plages réalistes"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                const = case_data["constantes"]

                # Fréquence cardiaque
                self.assertGreaterEqual(const["frequence_cardiaque"], 30)
                self.assertLessEqual(const["frequence_cardiaque"], 200)

                # Fréquence respiratoire
                self.assertGreaterEqual(const["frequence_respiratoire"], 5)
                self.assertLessEqual(const["frequence_respiratoire"], 50)

                # Saturation
                self.assertGreaterEqual(const["saturation_oxygene"], 60)
                self.assertLessEqual(const["saturation_oxygene"], 100)

                # Tension
                self.assertGreaterEqual(const["tension_systolique"], 50)
                self.assertLessEqual(const["tension_systolique"], 250)
                self.assertGreaterEqual(const["tension_diastolique"], 30)
                self.assertLessEqual(const["tension_diastolique"], 150)

                # Température
                self.assertGreaterEqual(const["temperature"], 34.0)
                self.assertLessEqual(const["temperature"], 42.0)

                # Glasgow
                self.assertGreaterEqual(const["glasgow"], 3)
                self.assertLessEqual(const["glasgow"], 15)

    def test_patient_creation_from_cases(self):
        """Teste la création de patients à partir des cas"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                # Créer patient
                patient = Patient(
                    age=case_data["age"],
                    motif_consultation=case_data["motif"],
                    constantes=Constantes(**case_data["constantes"])
                )

                # Vérifier
                self.assertEqual(patient.age, case_data["age"])
                self.assertEqual(patient.motif_consultation, case_data["motif"])
                self.assertIsNotNone(patient.constantes)

    def test_triage_returns_valid_result(self):
        """Teste que le triage retourne toujours un résultat valide"""
        for case_name, case_data in PREDEFINED_CASES.items():
            with self.subTest(case=case_name):
                patient = Patient(
                    age=case_data["age"],
                    motif_consultation=case_data["motif"],
                    constantes=Constantes(**case_data["constantes"])
                )

                result = self.agent.triage_patient(patient)

                # Vérifier structure du résultat
                self.assertIsNotNone(result.niveau_gravite)
                self.assertIsInstance(result.niveau_gravite, GravityLevel)
                self.assertIsNotNone(result.justification)
                self.assertIsInstance(result.justification, str)
                self.assertGreater(len(result.justification), 0)
                self.assertGreaterEqual(result.confiance, 0.0)
                self.assertLessEqual(result.confiance, 1.0)


if __name__ == "__main__":
    unittest.main()
