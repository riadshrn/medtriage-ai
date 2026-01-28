"""
Service de triage hybride (FRENCH + ML).

Combine les regles du protocole FRENCH avec un modele ML pour
fournir un triage robuste avec score de confiance.
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

import pandas as pd
import numpy as np

from api.ml.classifier import TriageClassifier
from api.ml.feature_config import (
    ALL_ML_FEATURES,
    PredictionQuality,
    assess_prediction_quality,
    DEFAULT_VALUES,
)
from api.services.french_triage import FrenchTriageEngine, ConstantesVitales
from api.schemas.triage import PatientInput

logger = logging.getLogger(__name__)


class TriageService:
    """Service de triage hybride combinant FRENCH et ML."""

    def __init__(self):
        self.ml_model_path = "models/trained/triage_model.json"
        self.ml_preprocessor_path = "models/trained/preprocessor.pkl"

        self.french_engine = FrenchTriageEngine()
        self._classifier: Optional[TriageClassifier] = None
        self.model_version = "v2.1.0-hybrid"
        self._ml_loaded = False

    def _load_ml_model(self) -> bool:
        """
        Charge le modele ML.

        Returns:
            True si charge avec succes, False sinon
        """
        if self._classifier is not None:
            return True

        try:
            self._classifier = TriageClassifier.load(
                model_path=self.ml_model_path,
                preprocessor_path=self.ml_preprocessor_path
            )
            self._ml_loaded = True
            logger.info(f"Modele ML charge: {self.ml_model_path}")
            return True
        except FileNotFoundError as e:
            logger.warning(f"Modele ML non trouve: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur chargement ML: {e}", exc_info=True)
            return False

    def _prepare_ml_features(self, patient: PatientInput) -> Dict[str, Any]:
        """
        Prepare les features pour le modele ML.

        Utilise feature_config pour garantir la coherence.

        Args:
            patient: Donnees du patient

        Returns:
            Dictionnaire des features
        """
        features = {
            'age': patient.age,
            'sexe': patient.sexe,
            'frequence_cardiaque': patient.constantes.frequence_cardiaque,
            'pression_systolique': patient.constantes.pression_systolique,
            'pression_diastolique': patient.constantes.pression_diastolique,
            'frequence_respiratoire': patient.constantes.frequence_respiratoire,
            'temperature': patient.constantes.temperature,
            'saturation_oxygene': patient.constantes.saturation_oxygene,
            'echelle_douleur': patient.constantes.echelle_douleur,
            # CORRECTION: On inclut maintenant glycemie
            'glycemie': patient.constantes.glycemie if patient.constantes.glycemie is not None else DEFAULT_VALUES['glycemie'],
            'glasgow': patient.constantes.glasgow if patient.constantes.glasgow is not None else DEFAULT_VALUES['glasgow'],
        }
        return features

    def _save_to_history(self, result: dict):
        """Sauvegarde le resultat dans l'historique."""
        try:
            history_path = Path("data/history.json")
            history_path.parent.mkdir(parents=True, exist_ok=True)

            with open(history_path, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    **result
                }) + "\n")
        except Exception as e:
            logger.warning(f"Erreur sauvegarde historique: {e}")

    def predict(self, patient: PatientInput) -> dict:
        """
        Effectue le triage d'un patient.

        Combine:
        1. Protocole FRENCH (regles medicales)
        2. Modele ML (classification)

        Args:
            patient: Donnees du patient

        Returns:
            Resultat du triage avec score de confiance
        """
        start_time = time.time()
        prediction_id = str(uuid.uuid4())[:8]

        # =========================================================
        # 1. FRENCH TRIAGE (toujours execute)
        # =========================================================
        constantes_legacy = ConstantesVitales(
            frequence_cardiaque=patient.constantes.frequence_cardiaque,
            frequence_respiratoire=patient.constantes.frequence_respiratoire,
            saturation_oxygene=patient.constantes.saturation_oxygene,
            pression_systolique=patient.constantes.pression_systolique,
            pression_diastolique=patient.constantes.pression_diastolique,
            temperature=patient.constantes.temperature,
            echelle_douleur=patient.constantes.echelle_douleur,
            glasgow=patient.constantes.glasgow
        )

        french_result = self.french_engine.triage(
            age=patient.age,
            sexe=patient.sexe,
            motif=patient.motif_consultation,
            constantes=constantes_legacy,
            antecedents=patient.antecedents
        )

        logger.info(
            f"[{prediction_id}] FRENCH: {french_result['gravity_level']} "
            f"({french_result['french_triage_level']})"
        )

        # =========================================================
        # 2. ML PREDICTION
        # =========================================================
        ml_score = 0.5
        ml_prediction = None
        prediction_quality = PredictionQuality.HIGH
        missing_features = []
        ml_error = None

        # Preparer les features
        features = self._prepare_ml_features(patient)

        # Evaluer la qualite des donnees
        prediction_quality, missing_features = assess_prediction_quality(features)

        if prediction_quality == PredictionQuality.INSUFFICIENT:
            logger.warning(
                f"[{prediction_id}] Donnees insuffisantes pour ML: {missing_features}"
            )
        else:
            # Tenter la prediction ML
            try:
                ml_loaded = self._load_ml_model()
                if ml_loaded and self._classifier:
                    df = pd.DataFrame([features])
                    y_pred, y_proba, latency = self._classifier.predict(df)
                    ml_prediction = y_pred[0]
                    ml_score = float(np.max(y_proba[0]))

                    logger.info(
                        f"[{prediction_id}] ML: {ml_prediction} "
                        f"(score={ml_score:.2f}, latency={latency*1000:.1f}ms)"
                    )
            except Exception as e:
                ml_error = str(e)
                logger.error(f"[{prediction_id}] Erreur ML: {e}", exc_info=True)

        # =========================================================
        # 3. CONSOLIDATION
        # =========================================================
        confidence = 0.75  # Base

        # Bonus si ML et FRENCH sont d'accord
        if ml_prediction and ml_prediction == french_result["gravity_level"]:
            confidence += 0.15
            logger.debug(f"[{prediction_id}] ML et FRENCH concordent (+15% confiance)")

        # Boost si red flags detectes
        if len(french_result["red_flags"]) > 0:
            confidence = 0.95

        # Penalite si qualite donnees basse
        if prediction_quality == PredictionQuality.LOW:
            confidence -= 0.10
        elif prediction_quality == PredictionQuality.INSUFFICIENT:
            confidence -= 0.20

        confidence = max(0.5, min(confidence, 0.99))

        # Justification
        justif = f"Niveau {french_result['french_triage_level']}."
        if french_result['red_flags']:
            justif += f" Alertes: {', '.join(french_result['red_flags'])}."
        if prediction_quality != PredictionQuality.HIGH:
            justif += f" Qualite donnees: {prediction_quality.value}."

        # Temps de traitement
        duration_ms = (time.time() - start_time) * 1000

        # =========================================================
        # 4. CONSTRUCTION REPONSE
        # =========================================================
        final_response = {
            "prediction_id": prediction_id,
            "gravity_level": french_result["gravity_level"],
            "french_triage_level": french_result["french_triage_level"],
            "confidence_score": confidence,
            "justification": justif,
            "red_flags": french_result["red_flags"],
            "recommendations": french_result["recommendations"],
            "orientation": french_result["orientation"],
            "delai_prise_en_charge": french_result["delai_prise_en_charge"],
            "model_version": self.model_version,
            "ml_score": ml_score,
            "processing_time_ms": duration_ms,
            # Nouveaux champs pour robustesse
            "prediction_quality": prediction_quality.value,
            "missing_features": missing_features,
            "ml_available": self._ml_loaded,
            "ml_error": ml_error,
        }

        logger.info(
            f"[{prediction_id}] Final: {final_response['gravity_level']} "
            f"(conf={confidence:.2f}, quality={prediction_quality.value}, "
            f"time={duration_ms:.1f}ms)"
        )

        self._save_to_history(final_response)
        return final_response

    def get_model_info(self) -> dict:
        """Retourne les informations sur le modele charge."""
        self._load_ml_model()

        return {
            "model_version": self.model_version,
            "ml_loaded": self._ml_loaded,
            "ml_model_path": self.ml_model_path,
            "features_used": ALL_ML_FEATURES,
        }


# Instance singleton
_service = TriageService()


def get_triage_service() -> TriageService:
    """Retourne l'instance du service de triage."""
    return _service
