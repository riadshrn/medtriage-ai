"""
Outils pour l'agent de triage.
"""

from typing import Dict, Optional, Tuple
from pathlib import Path

from src.ml import TriageClassifier
from src.llm import RAGEngine
from src.models import Patient, GravityLevel


class TriageTools:
    """
    Outils utilisés par l'agent de triage.

    Encapsule les appels au modèle ML et au système RAG/LLM.
    """

    def __init__(
        self,
        ml_model_path: str,
        ml_preprocessor_path: str,
        vector_store_path: Optional[str] = None,
        llm_model_name: str = "facebook/opt-350m",
    ):
        """
        Initialise les outils de triage.

        Args:
            ml_model_path: Chemin vers le modèle ML
            ml_preprocessor_path: Chemin vers le préprocesseur
            vector_store_path: Chemin vers le vector store (None = fallback)
            llm_model_name: Nom du modèle LLM Hugging Face
        """
        print("=" * 60)
        print("INITIALISATION DES OUTILS DE TRIAGE")
        print("=" * 60)

        # Chargement du modèle ML
        print("\nChargement du modele ML...")
        self.ml_classifier = TriageClassifier.load(
            ml_model_path, ml_preprocessor_path
        )

        # Initialisation du RAG Engine
        print("\nInitialisation du RAG Engine...")
        try:
            self.rag_engine = RAGEngine(
                vector_store_path=vector_store_path,
                llm_model_name=llm_model_name,
            )
        except Exception as e:
            print(f"Erreur lors du chargement du RAG : {e}")
            print("Le systeme utilisera des justifications basees sur des regles.")
            self.rag_engine = None

        print("\n" + "=" * 60)
        print("OUTILS DE TRIAGE PRETS")
        print("=" * 60)

    def predict_gravity(
        self, patient: Patient
    ) -> Tuple[str, float, Dict[str, float], float]:
        """
        Prédit le niveau de gravité avec le modèle ML.

        Args:
            patient: Patient à évaluer

        Returns:
            Tuple[gravity_level, confidence, probabilities, latency]:
                - gravity_level: Niveau prédit (GRIS/VERT/JAUNE/ROUGE)
                - confidence: Score de confiance (0-1)
                - probabilities: Probabilités pour chaque classe
                - latency: Temps de prédiction (secondes)
        """
        # Préparation des features au format attendu par le classifier
        patient_dict = patient.to_dict()

        # Aplatissement des constantes au niveau racine
        features = {
            "age": patient_dict["age"],
            "sexe": patient_dict["sexe"],
            **patient_dict["constantes"],  # Aplatir les constantes
        }

        # Prédiction
        gravity_level, confidence, probabilities, latency = (
            self.ml_classifier.predict_single(features)
        )

        return gravity_level, confidence, probabilities, latency

    def generate_justification(
        self,
        patient: Patient,
        gravity_level: str,
        confidence: float,
        use_rag: bool = True,
    ) -> Tuple[str, float]:
        """
        Génère une justification médicale.

        Args:
            patient: Patient évalué
            gravity_level: Niveau de gravité prédit
            confidence: Score de confiance du modèle ML
            use_rag: Utiliser le RAG (True) ou fallback (False)

        Returns:
            Tuple[justification, latency]:
                - justification: Texte de justification
                - latency: Temps de génération (secondes)
        """
        if self.rag_engine is None or not use_rag:
            # Fallback : justification basée sur règles
            return self._generate_rule_based_justification(
                patient, gravity_level, confidence
            ), 0.0

        # Préparation des données patient
        patient_data = patient.to_dict()

        # Génération avec RAG
        justification, latency, _ = self.rag_engine.generate_justification(
            patient_data=patient_data,
            gravity_level=gravity_level,
            confidence=confidence,
            use_rag=use_rag,
        )

        return justification, latency

    def _generate_rule_based_justification(
        self, patient: Patient, gravity_level: str, confidence: float
    ) -> str:
        """
        Génère une justification basée sur des règles simples (fallback).

        Args:
            patient: Patient évalué
            gravity_level: Niveau de gravité
            confidence: Score de confiance

        Returns:
            str: Justification générée
        """
        c = patient.constantes
        motif = patient.motif_consultation

        # Identification des anomalies
        anomalies = []

        if c.saturation_oxygene < 90:
            anomalies.append(f"hypoxémie sévère (SpO2 {c.saturation_oxygene}%)")
        elif c.saturation_oxygene < 94:
            anomalies.append(f"hypoxémie modérée (SpO2 {c.saturation_oxygene}%)")

        if c.frequence_cardiaque > 120:
            anomalies.append(f"tachycardie ({c.frequence_cardiaque} bpm)")
        elif c.frequence_cardiaque < 50:
            anomalies.append(f"bradycardie ({c.frequence_cardiaque} bpm)")

        if c.temperature > 39:
            anomalies.append(f"fièvre élevée ({c.temperature}°C)")
        elif c.temperature < 36:
            anomalies.append(f"hypothermie ({c.temperature}°C)")

        if c.echelle_douleur >= 7:
            anomalies.append(f"douleur intense ({c.echelle_douleur}/10)")

        # Construction de la justification selon le niveau
        if gravity_level == "ROUGE":
            if anomalies:
                return f"Patient en urgence vitale présentant {', '.join(anomalies[:2])} nécessitant une prise en charge immédiate."
            else:
                return f"Patient présentant {motif} avec signes de détresse vitale nécessitant une intervention médicale immédiate."

        elif gravity_level == "JAUNE":
            if anomalies:
                return f"Patient nécessitant une prise en charge rapide en raison de {', '.join(anomalies[:2])} associé à {motif}."
            else:
                return f"Patient présentant {motif} nécessitant une évaluation médicale rapide pour éviter une dégradation."

        elif gravity_level == "VERT":
            if anomalies:
                return f"Patient stable avec {', '.join(anomalies[:1])} et {motif}, consultation dans un délai standard."
            else:
                return f"Patient stable présentant {motif} pouvant attendre une consultation standard."

        else:  # GRIS
            return f"Patient stable sans signe de détresse présentant {motif}, prise en charge différée possible."
