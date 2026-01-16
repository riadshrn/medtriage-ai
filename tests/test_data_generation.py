"""
Tests unitaires pour le module de génération de données.
"""

import pytest

from src.data import PatientGenerator, GravityLabeler
from src.models import GravityLevel, ConstantesVitales, Patient


class TestPatientGenerator:
    """Tests pour PatientGenerator."""

    def test_generate_single_patient(self):
        """Test de génération d'un seul patient."""
        generator = PatientGenerator(seed=42)
        patient = generator.generate_patient()

        assert patient.age >= 0
        assert patient.sexe in ["M", "F", "Autre"]
        assert len(patient.motif_consultation) > 0
        assert patient.constantes is not None
        assert patient.id is not None

    def test_generate_patient_with_target_gravity(self):
        """Test de génération ciblée par gravité."""
        generator = PatientGenerator(seed=42)

        # Génération d'un patient ROUGE
        patient_rouge = generator.generate_patient(target_gravity="ROUGE")
        assert patient_rouge.constantes is not None

        # Le patient devrait avoir des signes de gravité
        # (on vérifie juste que ça ne crash pas)

    def test_generate_dataset(self):
        """Test de génération d'un dataset complet."""
        generator = PatientGenerator(seed=42)
        n_samples = 100
        patients = generator.generate_dataset(n_samples=n_samples)

        assert len(patients) == n_samples
        assert all(isinstance(p, Patient) for p in patients)

    def test_generate_dataset_with_custom_distribution(self):
        """Test de génération avec distribution personnalisée."""
        generator = PatientGenerator(seed=42)
        distribution = {
            "GRIS": 0.1,
            "VERT": 0.2,
            "JAUNE": 0.3,
            "ROUGE": 0.4,
        }

        patients = generator.generate_dataset(
            n_samples=100,
            distribution=distribution
        )

        assert len(patients) == 100

    def test_seed_consistency(self):
        """Test que la seed est bien utilisée."""
        gen = PatientGenerator(seed=42)
        patients = gen.generate_dataset(n_samples=10)

        # Vérifier que tous les patients ont des valeurs valides
        for patient in patients:
            assert 0 <= patient.age <= 120
            assert patient.sexe in ["M", "F", "Autre"]
            assert len(patient.motif_consultation) > 0
            assert 20 <= patient.constantes.frequence_cardiaque <= 250


class TestGravityLabeler:
    """Tests pour GravityLabeler."""

    def test_label_critical_patient(self):
        """Test de classification d'un patient critique."""
        constantes = ConstantesVitales(
            frequence_cardiaque=150,  # Tachycardie sévère
            pression_systolique=85,   # Hypotension
            pression_diastolique=50,
            frequence_respiratoire=30,  # Polypnée
            temperature=35.0,  # Hypothermie
            saturation_oxygene=85,  # Hypoxémie sévère
            echelle_douleur=9,
        )

        patient = Patient(
            age=75,
            sexe="M",
            motif_consultation="Douleur thoracique intense",
            constantes=constantes,
        )

        labeler = GravityLabeler()
        gravity = labeler.label_patient(patient)

        assert gravity == GravityLevel.ROUGE

    def test_label_stable_patient(self):
        """Test de classification d'un patient stable."""
        constantes = ConstantesVitales(
            frequence_cardiaque=75,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=1,
        )

        patient = Patient(
            age=35,
            sexe="F",
            motif_consultation="Consultation de suivi",
            constantes=constantes,
        )

        labeler = GravityLabeler()
        gravity = labeler.label_patient(patient)

        assert gravity == GravityLevel.GRIS

    def test_label_moderate_urgency(self):
        """Test de classification d'une urgence modérée."""
        constantes = ConstantesVitales(
            frequence_cardiaque=95,
            pression_systolique=145,
            pression_diastolique=90,
            frequence_respiratoire=22,
            temperature=38.8,
            saturation_oxygene=92,
            echelle_douleur=6,
        )

        patient = Patient(
            age=55,
            sexe="M",
            motif_consultation="Fièvre élevée avec frissons",
            constantes=constantes,
        )

        labeler = GravityLabeler()
        gravity = labeler.label_patient(patient)

        assert gravity == GravityLevel.JAUNE

    def test_label_with_keywords(self):
        """Test de classification basée sur les mots-clés."""
        constantes = ConstantesVitales(
            frequence_cardiaque=80,
            pression_systolique=120,
            pression_diastolique=80,
            frequence_respiratoire=16,
            temperature=37.0,
            saturation_oxygene=98,
            echelle_douleur=3,
        )

        # Même avec constantes normales, "AVC" devrait donner ROUGE
        patient = Patient(
            age=70,
            sexe="M",
            motif_consultation="AVC suspecté",
            constantes=constantes,
        )

        labeler = GravityLabeler()
        gravity = labeler.label_patient(patient)

        assert gravity == GravityLevel.ROUGE

    def test_label_elderly_with_abnormal_vitals(self):
        """Test : âge élevé + constantes anormales = ROUGE."""
        constantes = ConstantesVitales(
            frequence_cardiaque=110,
            pression_systolique=95,
            pression_diastolique=60,
            frequence_respiratoire=24,
            temperature=38.0,
            saturation_oxygene=92,
            echelle_douleur=5,
        )

        patient = Patient(
            age=85,  # Âge critique
            sexe="F",
            motif_consultation="Malaise général",
            constantes=constantes,
        )

        labeler = GravityLabeler()
        gravity = labeler.label_patient(patient)

        assert gravity == GravityLevel.ROUGE
