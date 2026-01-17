"""
Service de Triage combinant ML + Grille FRENCH

Ce service orchestre :
1. La grille FRENCH pour les règles métier
2. Le modèle ML pour la prédiction
3. Le RAG pour le contexte médical (optionnel)
"""

import sys
from pathlib import Path
from typing import Optional, List
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.api.services.french_triage import FrenchTriageEngine, ConstantesVitales, FrenchTriageLevel
from src.api.schemas.triage import PatientInput


class TriageService:
    """
    Service principal de triage

    Combine plusieurs sources d'analyse :
    - Grille FRENCH (règles expertes)
    - Modèle ML (apprentissage sur données)
    - RAG (contexte documentaire)
    """

    def __init__(
        self,
        ml_model_path: str = "models/trained/triage_model.json",
        ml_preprocessor_path: str = "models/trained/preprocessor.pkl",
        vector_store_path: Optional[str] = "data/vector_store/medical_kb.pkl"
    ):
        self.ml_model_path = ml_model_path
        self.ml_preprocessor_path = ml_preprocessor_path
        self.vector_store_path = vector_store_path

        # Grille FRENCH
        self.french_engine = FrenchTriageEngine()

        # ML Model (chargé à la demande)
        self._ml_model = None
        self._preprocessor = None

        # RAG (chargé à la demande)
        self._rag_engine = None

        # Version
        self.model_version = "v2.0.0-french"

    def _load_ml_model(self):
        """Charge le modèle ML si pas déjà fait"""
        if self._ml_model is None:
            try:
                import xgboost as xgb
                import pickle

                self._ml_model = xgb.XGBClassifier()
                self._ml_model.load_model(self.ml_model_path)

                with open(self.ml_preprocessor_path, 'rb') as f:
                    self._preprocessor = pickle.load(f)

                print(f"Modèle ML chargé: {self.ml_model_path}")
            except Exception as e:
                print(f"Erreur chargement modèle ML: {e}")
                self._ml_model = None

    def _load_rag(self):
        """Charge le RAG engine si pas déjà fait"""
        if self._rag_engine is None and self.vector_store_path:
            try:
                from src.rag.engine import RAGEngine
                self._rag_engine = RAGEngine(
                    vector_store_path=self.vector_store_path
                )
                print("RAG Engine initialisé")
            except Exception as e:
                print(f"Erreur chargement RAG: {e}")
                self._rag_engine = None

    def triage(self, patient: PatientInput, use_rag: bool = True) -> dict:
        """
        Effectue le triage complet d'un patient

        Pipeline :
        1. Évaluation FRENCH (constantes + motif)
        2. Prédiction ML
        3. Enrichissement RAG (optionnel)
        4. Fusion des résultats
        """
        start_time = time.time()

        # 1. Évaluation FRENCH
        constantes = ConstantesVitales(
            frequence_cardiaque=patient.constantes.frequence_cardiaque,
            frequence_respiratoire=patient.constantes.frequence_respiratoire,
            saturation_oxygene=patient.constantes.saturation_oxygene,
            pression_systolique=patient.constantes.pression_systolique,
            pression_diastolique=patient.constantes.pression_diastolique,
            temperature=patient.constantes.temperature,
            echelle_douleur=patient.constantes.echelle_douleur
        )

        french_result = self.french_engine.triage(
            age=patient.age,
            sexe=patient.sexe,
            motif=patient.motif_consultation,
            constantes=constantes,
            antecedents=patient.antecedents
        )

        # 2. Prédiction ML
        ml_score = 0.5
        ml_prediction = None
        try:
            self._load_ml_model()
            if self._ml_model is not None:
                ml_score, ml_prediction = self._predict_ml(patient)
        except Exception as e:
            print(f"Erreur prédiction ML: {e}")

        # 3. Enrichissement RAG
        rag_context = None
        rag_recommendations = []
        if use_rag:
            try:
                self._load_rag()
                if self._rag_engine is not None:
                    rag_result = self._rag_engine.query(
                        f"Patient {patient.age} ans, {patient.motif_consultation}. "
                        f"Constantes: FC {patient.constantes.frequence_cardiaque}, "
                        f"SpO2 {patient.constantes.saturation_oxygene}%, "
                        f"T° {patient.constantes.temperature}°C"
                    )
                    rag_context = rag_result.get("context", "")
                    rag_recommendations = rag_result.get("recommendations", [])
            except Exception as e:
                print(f"Erreur RAG: {e}")

        # 4. Fusion des résultats
        # La grille FRENCH est prioritaire (règles métier validées)
        # Le ML affine la confiance
        confidence_score = self._calculate_confidence(french_result, ml_score, ml_prediction)

        # Construire la justification
        justification = self._build_justification(
            french_result,
            patient,
            ml_prediction,
            rag_context
        )

        # Fusionner les recommandations
        all_recommendations = french_result["recommendations"].copy()
        if rag_recommendations:
            all_recommendations.extend([r for r in rag_recommendations if r not in all_recommendations])

        processing_time = (time.time() - start_time) * 1000

        return {
            "gravity_level": french_result["gravity_level"],
            "french_triage_level": french_result["french_triage_level"],
            "confidence_score": confidence_score,
            "ml_score": ml_score,
            "delai_prise_en_charge": french_result["delai_prise_en_charge"],
            "orientation": french_result["orientation"],
            "justification": justification,
            "red_flags": french_result["red_flags"],
            "recommendations": all_recommendations,
            "rag_context": rag_context,
            "model_version": self.model_version,
            "processing_time_ms": processing_time
        }

    def _predict_ml(self, patient: PatientInput) -> tuple:
        """Effectue la prédiction ML"""
        import pandas as pd
        import numpy as np

        # Préparer les features
        features = {
            'age': patient.age,
            'sexe': patient.sexe,
            'frequence_cardiaque': patient.constantes.frequence_cardiaque,
            'frequence_respiratoire': patient.constantes.frequence_respiratoire,
            'saturation_oxygene': patient.constantes.saturation_oxygene,
            'pression_systolique': patient.constantes.pression_systolique,
            'pression_diastolique': patient.constantes.pression_diastolique,
            'temperature': patient.constantes.temperature,
            'echelle_douleur': patient.constantes.echelle_douleur
        }

        df = pd.DataFrame([features])

        # Préprocessing
        if self._preprocessor:
            X = self._preprocessor.transform(df)
        else:
            # Fallback: encodage simple
            df['sexe'] = df['sexe'].map({'M': 0, 'F': 1})
            X = df.values

        # Prédiction
        probas = self._ml_model.predict_proba(X)[0]
        pred_idx = np.argmax(probas)
        confidence = float(probas[pred_idx])

        # Mapper l'index vers le niveau
        level_map = {0: "GRIS", 1: "VERT", 2: "JAUNE", 3: "ROUGE"}
        prediction = level_map.get(pred_idx, "JAUNE")

        return confidence, prediction

    def _calculate_confidence(self, french_result: dict, ml_score: float, ml_prediction: Optional[str]) -> float:
        """
        Calcule le score de confiance global

        Prend en compte :
        - L'accord entre FRENCH et ML
        - La gravité des alertes
        - La confiance du modèle ML
        """
        base_confidence = 0.7  # Confiance de base pour FRENCH

        # Bonus si ML et FRENCH sont d'accord
        if ml_prediction and ml_prediction == french_result["gravity_level"]:
            base_confidence += 0.15

        # Bonus basé sur le score ML
        base_confidence += ml_score * 0.1

        # Malus si beaucoup d'alertes contradictoires
        if len(french_result["red_flags"]) > 3:
            base_confidence -= 0.05

        return min(max(base_confidence, 0.5), 0.99)

    def _build_justification(
        self,
        french_result: dict,
        patient: PatientInput,
        ml_prediction: Optional[str],
        rag_context: Optional[str]
    ) -> str:
        """Construit la justification textuelle du triage"""
        parts = []

        # Catégorie et niveau
        parts.append(f"Catégorie: {french_result['categorie']}")
        parts.append(f"Niveau FRENCH: {french_result['french_triage_level']}")

        # Motif principal
        parts.append(f"Motif: {patient.motif_consultation}")

        # Alertes
        if french_result["red_flags"]:
            parts.append(f"Alertes: {', '.join(french_result['red_flags'])}")

        # Accord ML
        if ml_prediction:
            if ml_prediction == french_result["gravity_level"]:
                parts.append(f"Confirmé par le modèle ML")
            else:
                parts.append(f"Note: ML suggère niveau {ml_prediction}")

        return ". ".join(parts)
