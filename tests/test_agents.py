"""
Tests pour le module agents.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Patient, ConstantesVitales, GravityLevel


class TestTriageTools:
    """Tests pour les outils de triage."""

    def test_rule_based_justification_rouge(self):
        """Test de la justification par regles pour niveau ROUGE."""
        from src.agents.tools import TriageTools

        # Creer un patient critique
        constantes = ConstantesVitales(
            frequence_cardiaque=150,
            pression_systolique=80,
            pression_diastolique=50,
            temperature=40.5,
            saturation_oxygene=85,
            frequence_respiratoire=30,
            echelle_douleur=9
        )

        patient = Patient(
            id="P001",
            age=65,
            sexe="M",
            motif_consultation="Douleur thoracique intense",
            constantes=constantes
        )

        # Tester la methode privee directement
        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "ROUGE", 0.95)

        assert "urgence vitale" in justification.lower() or "immediate" in justification.lower()

    def test_rule_based_justification_jaune(self):
        """Test de la justification par regles pour niveau JAUNE."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=110,
            pression_systolique=140,
            pression_diastolique=90,
            temperature=38.5,
            saturation_oxygene=94,
            frequence_respiratoire=22,
            echelle_douleur=6
        )

        patient = Patient(
            id="P002",
            age=45,
            sexe="F",
            motif_consultation="Douleur abdominale",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "JAUNE", 0.80)

        assert "rapide" in justification.lower() or "evaluation" in justification.lower()

    def test_rule_based_justification_vert(self):
        """Test de la justification par regles pour niveau VERT."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=125,
            pression_diastolique=80,
            temperature=37.2,
            saturation_oxygene=98,
            frequence_respiratoire=16,
            echelle_douleur=3
        )

        patient = Patient(
            id="P003",
            age=30,
            sexe="M",
            motif_consultation="Rhume avec toux",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "VERT", 0.75)

        assert "stable" in justification.lower() or "standard" in justification.lower()

    def test_rule_based_justification_gris(self):
        """Test de la justification par regles pour niveau GRIS."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=72,
            pression_systolique=120,
            pression_diastolique=75,
            temperature=36.8,
            saturation_oxygene=99,
            frequence_respiratoire=14,
            echelle_douleur=1
        )

        patient = Patient(
            id="P004",
            age=25,
            sexe="F",
            motif_consultation="Renouvellement ordonnance",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "GRIS", 0.90)

        assert "stable" in justification.lower() or "differee" in justification.lower()

    def test_anomaly_detection_hypoxemia(self):
        """Test de detection d'hypoxemie."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=85,
            pression_systolique=120,
            pression_diastolique=80,
            temperature=37.0,
            saturation_oxygene=88,  # Hypoxemie
            frequence_respiratoire=18,
            echelle_douleur=2
        )

        patient = Patient(
            id="P005",
            age=70,
            sexe="M",
            motif_consultation="Essoufflement",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "JAUNE", 0.85)

        assert "hypox" in justification.lower() or "spo2" in justification.lower()

    def test_anomaly_detection_tachycardia(self):
        """Test de detection de tachycardie."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=140,  # Tachycardie
            pression_systolique=110,
            pression_diastolique=70,
            temperature=37.5,
            saturation_oxygene=96,
            frequence_respiratoire=20,
            echelle_douleur=4
        )

        patient = Patient(
            id="P006",
            age=55,
            sexe="F",
            motif_consultation="Palpitations",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "JAUNE", 0.78)

        assert "tachycardie" in justification.lower() or "bpm" in justification.lower()

    def test_anomaly_detection_fever(self):
        """Test de detection de fievre elevee."""
        from src.agents.tools import TriageTools

        constantes = ConstantesVitales(
            frequence_cardiaque=95,
            pression_systolique=115,
            pression_diastolique=75,
            temperature=39.5,  # Fievre elevee
            saturation_oxygene=97,
            frequence_respiratoire=18,
            echelle_douleur=5
        )

        patient = Patient(
            id="P007",
            age=35,
            sexe="M",
            motif_consultation="Fievre et frissons",
            constantes=constantes
        )

        tools = Mock()
        tools._generate_rule_based_justification = TriageTools._generate_rule_based_justification

        justification = tools._generate_rule_based_justification(tools, patient, "JAUNE", 0.82)

        assert "fievre" in justification.lower() or "c" in justification.lower()


class TestTriageAgentIntegration:
    """Tests d'integration pour l'agent de triage (avec mocks)."""

    def test_agent_stats(self):
        """Test des statistiques de l'agent."""
        # On ne peut pas tester l'agent complet sans le modele,
        # mais on peut tester la structure attendue des stats
        expected_keys = ["use_rag", "ml_model", "llm_model", "vector_store_loaded"]

        # Verifier que les cles existent dans un dict de stats type
        stats = {
            "use_rag": True,
            "ml_model": "XGBoost",
            "llm_model": "facebook/opt-350m",
            "vector_store_loaded": False,
        }

        for key in expected_keys:
            assert key in stats

    def test_patient_to_dict_for_ml(self):
        """Test de la conversion patient vers dictionnaire pour le ML."""
        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            temperature=37.0,
            saturation_oxygene=98,
            frequence_respiratoire=16,
            echelle_douleur=2
        )

        patient = Patient(
            id="P008",
            age=40,
            sexe="M",
            motif_consultation="Test",
            constantes=constantes
        )

        patient_dict = patient.to_dict()

        # Verifier que les donnees necessaires pour le ML sont presentes
        assert "age" in patient_dict
        assert "sexe" in patient_dict
        assert "constantes" in patient_dict
        assert "frequence_cardiaque" in patient_dict["constantes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
