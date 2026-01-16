"""
Tests unitaires pour les modèles de données.
"""

import pytest
from datetime import datetime

from src.models import GravityLevel, ConstantesVitales, Patient, TriageResult


class TestGravityLevel:
    """Tests pour GravityLevel."""

    def test_priority_order(self):
        """Test de l'ordre de priorité."""
        assert GravityLevel.ROUGE.priority == 1
        assert GravityLevel.JAUNE.priority == 2
        assert GravityLevel.VERT.priority == 3
        assert GravityLevel.GRIS.priority == 4

    def test_descriptions(self):
        """Test des descriptions."""
        assert "immédiate" in GravityLevel.ROUGE.description.lower()
        assert "urgent" in GravityLevel.JAUNE.description.lower()

    def test_string_representation(self):
        """Test de la représentation string."""
        assert str(GravityLevel.ROUGE) == "ROUGE"


class TestConstantesVitales:
    """Tests pour ConstantesVitales."""

    def test_valid_constantes(self):
        """Test de création de constantes valides."""
        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=3,
        )
        assert constantes.frequence_cardiaque == 80
        assert constantes.temperature == 37.0

    def test_invalid_frequence_cardiaque(self):
        """Test de validation de la fréquence cardiaque."""
        with pytest.raises(ValueError, match="Fréquence cardiaque invalide"):
            ConstantesVitales(
                frequence_cardiaque=300,  # Trop élevé
                pression_systolique=120,
                pression_diastolique=80,
                frequence_respiratoire=16,
                temperature=37.0,
                saturation_oxygene=98,
                echelle_douleur=3,
            )

    def test_invalid_temperature(self):
        """Test de validation de la température."""
        with pytest.raises(ValueError, match="Température invalide"):
            ConstantesVitales(
                frequence_cardiaque=80,
                pression_systolique=120,
                pression_diastolique=80,
                frequence_respiratoire=16,
                temperature=50.0,  # Trop élevé
                saturation_oxygene=98,
                echelle_douleur=3,
            )

    def test_to_dict(self):
        """Test de conversion en dictionnaire."""
        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=3,
            glycemie=1.2,
        )
        data = constantes.to_dict()
        assert data["frequence_cardiaque"] == 80
        assert data["glycemie"] == 1.2


class TestPatient:
    """Tests pour Patient."""

    @pytest.fixture
    def constantes_valides(self):
        """Fixture de constantes vitales valides."""
        return ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=3,
        )

    def test_valid_patient(self, constantes_valides):
        """Test de création d'un patient valide."""
        patient = Patient(
            age=45,
            sexe="M",
            motif_consultation="Douleur thoracique",
            constantes=constantes_valides,
        )
        assert patient.age == 45
        assert patient.sexe == "M"
        assert patient.id is not None  # UUID généré

    def test_invalid_age(self, constantes_valides):
        """Test de validation de l'âge."""
        with pytest.raises(ValueError, match="Âge invalide"):
            Patient(
                age=150,  # Trop élevé
                sexe="M",
                motif_consultation="Test",
                constantes=constantes_valides,
            )

    def test_invalid_sexe(self, constantes_valides):
        """Test de validation du sexe."""
        with pytest.raises(ValueError, match="Sexe invalide"):
            Patient(
                age=45,
                sexe="X",  # Invalide
                motif_consultation="Test",
                constantes=constantes_valides,
            )

    def test_empty_motif(self, constantes_valides):
        """Test de validation du motif de consultation."""
        with pytest.raises(ValueError, match="motif de consultation"):
            Patient(
                age=45,
                sexe="M",
                motif_consultation="   ",  # Vide
                constantes=constantes_valides,
            )

    def test_to_dict(self, constantes_valides):
        """Test de conversion en dictionnaire."""
        patient = Patient(
            age=45,
            sexe="M",
            motif_consultation="Douleur thoracique",
            constantes=constantes_valides,
            antecedents="Hypertension",
        )
        data = patient.to_dict()
        assert data["age"] == 45
        assert data["antecedents"] == "Hypertension"
        assert "constantes" in data


class TestTriageResult:
    """Tests pour TriageResult."""

    @pytest.fixture
    def patient_valide(self):
        """Fixture de patient valide."""
        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=3,
        )
        return Patient(
            age=45,
            sexe="M",
            motif_consultation="Douleur thoracique",
            constantes=constantes,
        )

    def test_valid_triage_result(self, patient_valide):
        """Test de création d'un résultat de triage valide."""
        result = TriageResult(
            patient=patient_valide,
            gravity_level=GravityLevel.JAUNE,
            justification="Douleur thoracique nécessitant une évaluation rapide.",
            confidence_score=0.85,
            latency_ml=0.12,
            latency_llm=0.45,
        )
        assert result.gravity_level == GravityLevel.JAUNE
        assert result.confidence_score == 0.85

    def test_invalid_confidence_score(self, patient_valide):
        """Test de validation du score de confiance."""
        with pytest.raises(ValueError, match="Score de confiance invalide"):
            TriageResult(
                patient=patient_valide,
                gravity_level=GravityLevel.JAUNE,
                justification="Test",
                confidence_score=1.5,  # Trop élevé
            )

    def test_empty_justification(self, patient_valide):
        """Test de validation de la justification."""
        with pytest.raises(ValueError, match="justification"):
            TriageResult(
                patient=patient_valide,
                gravity_level=GravityLevel.JAUNE,
                justification="   ",  # Vide
                confidence_score=0.85,
            )

    def test_total_latency(self, patient_valide):
        """Test du calcul de la latence totale."""
        result = TriageResult(
            patient=patient_valide,
            gravity_level=GravityLevel.JAUNE,
            justification="Test",
            confidence_score=0.85,
            latency_ml=0.12,
            latency_llm=0.45,
        )
        assert result.total_latency == pytest.approx(0.57)

    def test_to_dict(self, patient_valide):
        """Test de conversion en dictionnaire."""
        result = TriageResult(
            patient=patient_valide,
            gravity_level=GravityLevel.ROUGE,
            justification="Urgence vitale",
            confidence_score=0.95,
        )
        data = result.to_dict()
        assert data["gravity_level"] == "ROUGE"
        assert data["confidence_score"] == 0.95
        assert "patient" in data
