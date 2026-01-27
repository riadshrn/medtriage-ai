"""
Service de triage basé sur le modèle XGBoost.

Utilise le modèle ML entraîné sur la grille FRENCH comme source principale
de prédiction, avec enrichissement clinique pour les recommandations.
"""

import time
from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.api.ml.classifier import TriageClassifier
from src.api.schemas.triage import PatientInput
from src.api.services.french_triage import (
    DELAI_PRISE_EN_CHARGE,
    FRENCH_TO_GRAVITY,
    ORIENTATION,
    ConstantesVitales,
    FrenchTriageEngine,
    FrenchTriageLevel,
    GravityLevel,
)


# Mapping inverse: gravity -> french triage level (niveau par défaut)
GRAVITY_TO_FRENCH = {
    GravityLevel.ROUGE: FrenchTriageLevel.TRI_2,
    GravityLevel.JAUNE: FrenchTriageLevel.TRI_3B,
    GravityLevel.VERT: FrenchTriageLevel.TRI_4,
    GravityLevel.GRIS: FrenchTriageLevel.TRI_5,
}


class TriageService:
    """Service de triage utilisant XGBoost comme moteur principal."""

    def __init__(self) -> None:
        self.ml_model_path = "models/trained/triage_model.json"
        self.ml_preprocessor_path = "models/trained/preprocessor.pkl"
        self._classifier: Optional[TriageClassifier] = None
        self._french_engine: Optional[FrenchTriageEngine] = None
        self.model_version = "v3.0.0-xgboost"

    @property
    def classifier(self) -> Optional[TriageClassifier]:
        """Lazy loading du modèle XGBoost."""
        if self._classifier is None:
            try:
                self._classifier = TriageClassifier.load(
                    model_path=self.ml_model_path,
                    preprocessor_path=self.ml_preprocessor_path
                )
            except Exception as e:
                print(f"Erreur chargement XGBoost: {e}")
        return self._classifier

    @property
    def french_engine(self) -> FrenchTriageEngine:
        """Lazy loading du moteur FRENCH (pour contexte clinique)."""
        if self._french_engine is None:
            self._french_engine = FrenchTriageEngine()
        return self._french_engine

    def _build_features(self, patient: PatientInput) -> pd.DataFrame:
        """Construit le DataFrame de features pour XGBoost."""
        return pd.DataFrame([{
            'age': patient.age,
            'sexe': patient.sexe,
            'motif_consultation': patient.motif_consultation,
            'frequence_cardiaque': patient.constantes.frequence_cardiaque,
            'pression_systolique': patient.constantes.pression_systolique,
            'pression_diastolique': patient.constantes.pression_diastolique,
            'frequence_respiratoire': patient.constantes.frequence_respiratoire,
            'temperature': patient.constantes.temperature,
            'saturation_oxygene': patient.constantes.saturation_oxygene,
            'echelle_douleur': patient.constantes.echelle_douleur,
        }])

    def _get_clinical_context(self, patient: PatientInput) -> Dict:
        """Récupère le contexte clinique via FRENCH (red_flags, recommandations)."""
        constantes = ConstantesVitales(
            frequence_cardiaque=patient.constantes.frequence_cardiaque,
            frequence_respiratoire=patient.constantes.frequence_respiratoire,
            saturation_oxygene=patient.constantes.saturation_oxygene,
            pression_systolique=patient.constantes.pression_systolique,
            pression_diastolique=patient.constantes.pression_diastolique,
            temperature=patient.constantes.temperature,
            echelle_douleur=patient.constantes.echelle_douleur,
            glasgow=patient.constantes.glasgow
        )
        return self.french_engine.triage(
            age=patient.age,
            sexe=patient.sexe,
            motif=patient.motif_consultation,
            constantes=constantes,
            antecedents=patient.antecedents
        )

    def predict(self, patient: PatientInput) -> Dict:
        """Prédit le niveau de triage via XGBoost."""
        start_time = time.time()

        # Prédiction XGBoost (source principale)
        gravity_level = GravityLevel.VERT
        confidence = 0.5

        if self.classifier:
            df = self._build_features(patient)
            y_pred, y_proba, _ = self.classifier.predict(df)
            gravity_level = GravityLevel(y_pred[0])
            confidence = float(np.max(y_proba[0]))

        # Contexte clinique FRENCH (alertes et recommandations)
        clinical = self._get_clinical_context(patient)

        # Mapping vers niveau FRENCH détaillé
        french_level = GRAVITY_TO_FRENCH[gravity_level]

        # Ajustement si comorbidités (3B -> 3A)
        if french_level == FrenchTriageLevel.TRI_3B and patient.antecedents:
            comorbidites = ["diabète", "insuffisance cardiaque", "cancer", "dialyse"]
            if any(c in " ".join(patient.antecedents).lower() for c in comorbidites):
                french_level = FrenchTriageLevel.TRI_3A

        # Upgrade si red_flags critiques
        if clinical["red_flags"]:
            confidence = max(confidence, 0.90)

        duration_ms = (time.time() - start_time) * 1000

        return {
            "gravity_level": gravity_level.value,
            "french_triage_level": french_level.value,
            "confidence_score": min(confidence, 0.99),
            "justification": f"Prédiction XGBoost: {gravity_level.value}. {', '.join(clinical['red_flags']) if clinical['red_flags'] else 'Pas d alertes.'}",
            "red_flags": clinical["red_flags"],
            "recommendations": clinical["recommendations"],
            "orientation": ORIENTATION[french_level],
            "delai_prise_en_charge": DELAI_PRISE_EN_CHARGE[french_level],
            "model_version": self.model_version,
            "ml_score": confidence,
            "processing_time_ms": duration_ms,
        }


_service = TriageService()


def get_triage_service() -> TriageService:
    """Retourne l'instance singleton du service."""
    return _service