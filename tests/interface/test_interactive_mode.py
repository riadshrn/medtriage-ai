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
    generate_patient_response
)
from src.models.triage_result import GravityLevel


class TestInteractiveMode(unittest.TestCase):
    """Tests pour le mode interactif"""

    def test_generate_patient_persona_rouge(self):
        """Teste la génération d'un patient ROUGE"""
        persona = generate_patient_persona("🔥 Urgence Vitale (Rouge)")

        self.assertIn("age", persona)
        self.assertIn("motif_reel", persona)
        self.assertIn("symptomes", persona)
        self.assertIn("constantes", persona)
        self.assertIn("expected_level", persona)

        self.assertEqual(persona["expected_level"], GravityLevel.ROUGE)
        self.assertIsInstance(persona["symptomes"], list)
        self.assertGreater(len(persona["symptomes"]), 0)

    def test_generate_patient_persona_orange(self):
        """Teste la génération d'un patient ORANGE"""
        persona = generate_patient_persona("⚡ Urgence (Orange)")

        self.assertEqual(persona["expected_level"], GravityLevel.ORANGE)
        self.assertIsInstance(persona["constantes"], dict)

    def test_generate_patient_persona_jaune(self):
        """Teste la génération d'un patient JAUNE"""
        persona = generate_patient_persona("⏰ Peu Urgent (Jaune)")

        self.assertEqual(persona["expected_level"], GravityLevel.JAUNE)

    def test_generate_patient_persona_vert(self):
        """Teste la génération d'un patient VERT"""
        persona = generate_patient_persona("✅ Non Urgent (Vert)")

        self.assertEqual(persona["expected_level"], GravityLevel.VERT)

    def test_generate_patient_persona_edge_case(self):
        """Teste la génération d'un cas limite"""
        persona = generate_patient_persona("🧪 Cas Limite (Edge Case)")

        self.assertIsNotNone(persona)
        self.assertIn("constantes", persona)

        # Vérifier que les constantes sont contradictoires
        const = persona["constantes"]
        self.assertIsNotNone(const["frequence_cardiaque"])
        self.assertIsNotNone(const["frequence_respiratoire"])

    def test_generate_patient_persona_anxious(self):
        """Teste la génération d'un patient anxieux"""
        persona = generate_patient_persona("🎭 Simulation d'Anxiété")

        self.assertIn("anxieux", persona["personnalite"].lower())
        self.assertEqual(persona["expected_level"], GravityLevel.JAUNE)

    def test_generate_patient_persona_minimizing(self):
        """Teste la génération d'un patient minimisant"""
        persona = generate_patient_persona("🤥 Patient Minimisant")

        self.assertIn("minimise", persona["personnalite"].lower())

    def test_generate_patient_persona_exaggerating(self):
        """Teste la génération d'un patient exagérant"""
        persona = generate_patient_persona("😱 Patient Exagérant")

        self.assertIn("dramatique", persona["personnalite"].lower())
        self.assertEqual(persona["expected_level"], GravityLevel.GRIS)

    def test_generate_patient_persona_random(self):
        """Teste la génération aléatoire"""
        persona = generate_patient_persona("🎲 Aléatoire (généré par LLM)")

        # Doit retourner un persona valide
        self.assertIsNotNone(persona)
        self.assertIn("expected_level", persona)

    def test_get_initial_patient_message(self):
        """Teste la génération du message initial"""
        for level in GravityLevel:
            with self.subTest(level=level):
                persona = {"expected_level": level}
                message = get_initial_patient_message(persona)

                self.assertIsInstance(message, str)
                self.assertGreater(len(message), 0)

    def test_get_initial_patient_message_rouge_urgent(self):
        """Teste que le message ROUGE est urgent"""
        persona = {"expected_level": GravityLevel.ROUGE}
        message = get_initial_patient_message(persona)

        # Doit contenir des mots urgents
        urgent_words = ["aidez", "mal", "très", "respirer"]
        has_urgent = any(word in message.lower() for word in urgent_words)
        self.assertTrue(has_urgent, f"Message not urgent: {message}")

    def test_get_initial_patient_message_gris_calm(self):
        """Teste que le message GRIS est calme"""
        persona = {"expected_level": GravityLevel.GRIS}
        message = get_initial_patient_message(persona)

        # Ne doit pas être dramatique
        self.assertNotIn("!!!", message)
        calm_words = ["bonjour", "grand chose", "pas"]
        has_calm = any(word in message.lower() for word in calm_words)
        self.assertTrue(has_calm)

    def test_generate_patient_response_symptom_question(self):
        """Teste la réponse à une question sur les symptômes"""
        persona = {
            "symptomes": ["Douleur thoracique", "Essoufflement"],
            "personnalite": "Patient calme",
            "expected_level": GravityLevel.ORANGE
        }

        response = generate_patient_response(
            persona,
            [],
            "Pouvez-vous me décrire vos symptômes ?"
        )

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        # Doit mentionner au moins un symptôme
        self.assertTrue(
            any(symptom.lower() in response.lower() for symptom in persona["symptomes"])
        )

    def test_generate_patient_response_duration_question(self):
        """Teste la réponse à une question sur la durée"""
        persona = {
            "expected_level": GravityLevel.ROUGE
        }

        response = generate_patient_response(
            persona,
            [],
            "Depuis quand avez-vous ces symptômes ?"
        )

        self.assertIsInstance(response, str)
        # Doit mentionner une durée
        time_words = ["depuis", "minutes", "heures", "jours"]
        has_time = any(word in response.lower() for word in time_words)
        self.assertTrue(has_time)

    def test_generate_patient_response_medical_history(self):
        """Teste la réponse à une question sur les antécédents"""
        persona = {
            "expected_level": GravityLevel.JAUNE
        }

        response = generate_patient_response(
            persona,
            [],
            "Avez-vous des antécédents médicaux ?"
        )

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_generate_patient_response_pain_scale(self):
        """Teste la réponse à une question sur l'échelle de douleur"""
        persona = {
            "expected_level": GravityLevel.ROUGE
        }

        response = generate_patient_response(
            persona,
            [],
            "Sur une échelle de 1 à 10, comment évaluez-vous la douleur ?"
        )

        self.assertIsInstance(response, str)
        # Doit contenir un chiffre
        has_number = any(char.isdigit() for char in response)
        self.assertTrue(has_number)

    def test_generate_patient_response_vitals(self):
        """Teste la réponse à une question sur les constantes"""
        persona = {
            "constantes": {
                "frequence_cardiaque": 120,
                "saturation_oxygene": 95
            }
        }

        response = generate_patient_response(
            persona,
            [],
            "Je vais prendre vos constantes vitales"
        )

        self.assertIsInstance(response, str)
        # Doit accepter
        accept_words = ["oui", "d'accord", "allez"]
        has_accept = any(word in response.lower() for word in accept_words)
        self.assertTrue(has_accept)

    def test_generate_patient_response_anxious_personality(self):
        """Teste que les patients anxieux dramatisent"""
        persona = {
            "symptomes": ["Palpitations"],
            "personnalite": "Patient très anxieux, dramatise",
            "expected_level": GravityLevel.JAUNE
        }

        response = generate_patient_response(
            persona,
            [],
            "Qu'est-ce qui vous amène ?"
        )

        # Doit contenir des exclamations ou être dramatique
        is_dramatic = "!" in response or "très" in response.lower() or "terrible" in response.lower()
        self.assertTrue(is_dramatic, f"Response not dramatic: {response}")

    def test_generate_patient_response_minimizing_personality(self):
        """Teste que les patients minimisants sous-estiment"""
        persona = {
            "symptomes": ["Douleur thoracique"],
            "personnalite": "Patient stoïque, minimise ses symptômes",
            "expected_level": GravityLevel.ORANGE
        }

        response = generate_patient_response(
            persona,
            [],
            "Qu'est-ce qui vous amène ?"
        )

        # Doit minimiser
        minimizing_words = ["rien", "pas grand chose", "juste", "petite"]
        has_minimizing = any(word in response.lower() for word in minimizing_words)
        self.assertTrue(has_minimizing, f"Response not minimizing: {response}")

    def test_constantes_completeness(self):
        """Teste que toutes les constantes requises sont présentes"""
        required_constantes = [
            "frequence_cardiaque",
            "frequence_respiratoire",
            "saturation_oxygene",
            "tension_systolique",
            "tension_diastolique",
            "temperature",
            "glasgow"
        ]

        patient_types = [
            "🔥 Urgence Vitale (Rouge)",
            "⚡ Urgence (Orange)",
            "⏰ Peu Urgent (Jaune)",
            "✅ Non Urgent (Vert)",
            "🎭 Simulation d'Anxiété"
        ]

        for patient_type in patient_types:
            with self.subTest(patient_type=patient_type):
                persona = generate_patient_persona(patient_type)
                constantes = persona["constantes"]

                for key in required_constantes:
                    self.assertIn(key, constantes, f"Missing {key} in {patient_type}")
                    self.assertIsNotNone(constantes[key])

    def test_all_patient_types_valid(self):
        """Teste que tous les types de patients sont valides"""
        patient_types = [
            "🎲 Aléatoire (généré par LLM)",
            "🔥 Urgence Vitale (Rouge)",
            "⚡ Urgence (Orange)",
            "⏰ Peu Urgent (Jaune)",
            "✅ Non Urgent (Vert)",
            "🧪 Cas Limite (Edge Case)",
            "🎭 Simulation d'Anxiété",
            "🤥 Patient Minimisant",
            "😱 Patient Exagérant"
        ]

        for patient_type in patient_types:
            with self.subTest(patient_type=patient_type):
                persona = generate_patient_persona(patient_type)

                # Vérifier structure
                self.assertIn("age", persona)
                self.assertIn("constantes", persona)
                self.assertIn("expected_level", persona)

                # Vérifier types
                self.assertIsInstance(persona["age"], int)
                self.assertIsInstance(persona["constantes"], dict)
                self.assertIsInstance(persona["expected_level"], GravityLevel)


if __name__ == "__main__":
    unittest.main()
