"""
Agent principal de triage des patients.
"""

import time
from typing import Optional
from datetime import datetime

from src.models import Patient, TriageResult, GravityLevel
from .tools import TriageTools


class TriageAgent:
    """
    Agent intelligent de triage des patients aux urgences.

    Coordonne :
    1. La prédiction ML (niveau de gravité)
    2. La génération de justification (RAG + LLM)
    3. La construction du résultat complet
    """

    def __init__(
        self,
        ml_model_path: str,
        ml_preprocessor_path: str,
        vector_store_path: Optional[str] = None,
        llm_model_name: str = "facebook/opt-350m",
        use_rag: bool = True,
    ):
        """
        Initialise l'agent de triage.

        Args:
            ml_model_path: Chemin vers le modèle ML
            ml_preprocessor_path: Chemin vers le préprocesseur
            vector_store_path: Chemin vers le vector store (None = pas de RAG)
            llm_model_name: Nom du modèle LLM
            use_rag: Utiliser le RAG pour les justifications
        """
        self.use_rag = use_rag

        # Initialisation des outils
        self.tools = TriageTools(
            ml_model_path=ml_model_path,
            ml_preprocessor_path=ml_preprocessor_path,
            vector_store_path=vector_store_path,
            llm_model_name=llm_model_name,
        )

        print("\nAgent de triage initialise et pret.")

    def triage(self, patient: Patient, verbose: bool = False) -> TriageResult:
        """
        Effectue le triage complet d'un patient.

        Args:
            patient: Patient à évaluer
            verbose: Afficher les détails du processus

        Returns:
            TriageResult: Résultat complet du triage
        """
        if verbose:
            print("\n" + "=" * 60)
            print("TRIAGE EN COURS")
            print("=" * 60)
            print(f"\nPatient : {patient.age} ans, {patient.sexe}")
            print(f"Motif   : {patient.motif_consultation}")
            print(f"FC={patient.constantes.frequence_cardiaque} bpm, "
                  f"PA={patient.constantes.pression_systolique}/{patient.constantes.pression_diastolique} mmHg")
            print(f"SpO2={patient.constantes.saturation_oxygene}%, "
                  f"T={patient.constantes.temperature}°C, "
                  f"Douleur={patient.constantes.echelle_douleur}/10")

        # Étape 1 : Prédiction ML
        if verbose:
            print("\n[1/2] Prediction du niveau de gravite (ML)...")

        gravity_str, confidence, probabilities, ml_latency = (
            self.tools.predict_gravity(patient)
        )

        gravity_level = GravityLevel(gravity_str)

        if verbose:
            print(f"      Niveau predit : {gravity_level.value}")
            print(f"      Confiance     : {confidence:.0%}")
            print(f"      Latence ML    : {ml_latency * 1000:.2f}ms")

        # Étape 2 : Génération de justification
        if verbose:
            print(f"\n[2/2] Generation de la justification {'(RAG + LLM)' if self.use_rag else '(regles)'}...")

        justification, llm_latency = self.tools.generate_justification(
            patient=patient,
            gravity_level=gravity_str,
            confidence=confidence,
            use_rag=self.use_rag,
        )

        if verbose:
            print(f"      Justification generee")
            print(f"      Latence LLM   : {llm_latency * 1000:.2f}ms")

        # Construction du résultat
        result = TriageResult(
            patient=patient,
            gravity_level=gravity_level,
            justification=justification,
            confidence_score=confidence,
            ml_probabilities=probabilities,
            latency_ml=ml_latency,
            latency_llm=llm_latency,
        )

        if verbose:
            print("\n" + "=" * 60)
            print("TRIAGE TERMINE")
            print("=" * 60)
            print(f"\nRESULTAT : {gravity_level.value} (confiance: {confidence:.0%})")
            print(f"Temps total : {result.total_latency * 1000:.2f}ms")
            print(f"\nJUSTIFICATION :")
            print(f"  {justification}")
            print("\n" + "=" * 60)

        return result

    def batch_triage(
        self, patients: list[Patient], verbose: bool = False
    ) -> list[TriageResult]:
        """
        Effectue le triage d'un batch de patients.

        Args:
            patients: Liste de patients à évaluer
            verbose: Afficher les détails

        Returns:
            list[TriageResult]: Résultats de triage
        """
        results = []
        start_time = time.time()

        for i, patient in enumerate(patients, 1):
            if verbose:
                print(f"\n{'='*60}")
                print(f"Patient {i}/{len(patients)}")
                print(f"{'='*60}")

            result = self.triage(patient, verbose=verbose)
            results.append(result)

        total_time = time.time() - start_time

        if verbose:
            print(f"\n{'='*60}")
            print("BATCH TERMINE")
            print(f"{'='*60}")
            print(f"  Patients traites : {len(patients)}")
            print(f"  Temps total      : {total_time:.2f}s")
            print(f"  Temps moyen      : {total_time / len(patients) * 1000:.0f}ms/patient")

        return results

    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur l'agent.

        Returns:
            dict: Statistiques
        """
        return {
            "use_rag": self.use_rag,
            "ml_model": "XGBoost",
            "llm_model": "facebook/opt-350m" if self.tools.rag_engine else "Rule-based",
            "vector_store_loaded": self.tools.rag_engine is not None,
        }
