"""
Tests pour le mode interactif
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.interactive_mode import (
    generate_patient_persona,
    get_initial_patient_message,
)
from src.models.gravity_level import GravityLevel


class TestInteractiveMode(unittest.TestCase):
    """Tests pour le mode interactif"""

    def test_generate_patient_persona_structure(self):
        """Teste la structure d'un persona genere"""
        # Utiliser un profil qui fonctionne
        persona = generate_patient_persona("Consultation Standard (Vert)")

        # Verifier la structure
        self.assertIn("age", persona)
        self.assertIn("motif_reel", persona)
        self.assertIn("symptomes", persona)
        self.assertIn("constantes", persona)
        self.assertIn("expected_level", persona)

    def test_patient_persona_age_valid(self):
        """Teste que l'age du persona est valide"""
        persona = generate_patient_persona("Consultation Standard (Vert)")

        self.assertGreaterEqual(persona["age"], 0)
        self.assertLessEqual(persona["age"], 120)

    def test_patient_persona_motif_exists(self):
        """Teste que le motif existe"""
        persona = generate_patient_persona("Consultation Standard (Vert)")

        self.assertIsInstance(persona["motif_reel"], str)
        self.assertGreater(len(persona["motif_reel"]), 0)

    def test_patient_persona_constantes_valid(self):
        """Teste que les constantes du persona sont valides"""
        persona = generate_patient_persona("Consultation Standard (Vert)")
        constantes = persona["constantes"]

        self.assertIn("frequence_cardiaque", constantes)
        self.assertIn("saturation_oxygene", constantes)
        self.assertIn("temperature", constantes)

        # Verifier les plages
        self.assertGreater(constantes["frequence_cardiaque"], 0)
        self.assertLessEqual(constantes["frequence_cardiaque"], 250)
        self.assertGreaterEqual(constantes["saturation_oxygene"], 0)
        self.assertLessEqual(constantes["saturation_oxygene"], 100)

    def test_patient_persona_expected_level_is_gravity(self):
        """Teste que le niveau attendu est un GravityLevel"""
        persona = generate_patient_persona("Consultation Standard (Vert)")

        self.assertIsInstance(persona["expected_level"], GravityLevel)

    def test_get_initial_patient_message(self):
        """Teste le message initial du patient"""
        persona = generate_patient_persona("Consultation Standard (Vert)")
        message = get_initial_patient_message(persona)

        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)

    def test_get_initial_patient_message_contains_context(self):
        """Teste que le message initial contient du contexte"""
        persona = generate_patient_persona("Consultation Standard (Vert)")
        message = get_initial_patient_message(persona)

        # Le message devrait mentionner quelque chose
        # (peut etre vague mais pas vide)
        self.assertGreater(len(message), 10)


if __name__ == "__main__":
    unittest.main()
