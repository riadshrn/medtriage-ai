import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Imports internes
from src.api.ml.classifier import TriageClassifier
from src.api.services.french_triage import FrenchTriageEngine, ConstantesVitales
from src.api.schemas.triage import PatientInput

class TriageService:
    def __init__(self):
        self.ml_model_path = "models/trained/triage_model.json"
        self.ml_preprocessor_path = "models/trained/preprocessor.pkl"
        
        self.french_engine = FrenchTriageEngine()
        self._classifier = None 
        self.model_version = "v2.0.0-hybrid"

    def _load_ml_model(self):
        if self._classifier is None:
            try:
                self._classifier = TriageClassifier.load(
                    model_path=self.ml_model_path,
                    preprocessor_path=self.ml_preprocessor_path
                )
            except Exception as e:
                print(f"⚠️ Erreur chargement ML : {e}")

    def _save_to_history(self, result: dict):
        """Sauvegarde simple"""
        try:
            with open("data/history.json", "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    **result
                }) + "\n")
        except Exception:
            pass

    def predict(self, patient: PatientInput) -> dict:
        start_time = time.time() # <--- START CHRONO

        # 1. FRENCH TRIAGE
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

        # 2. ML PREDICTION
        ml_score = 0.5
        ml_prediction = None
        
        try:
            self._load_ml_model()
            if self._classifier:
                # --- CORRECTION COLONNES ICI (On retire glycemie) ---
                features = {
                    'age': patient.age,
                    'sexe': patient.sexe,
                    'motif_consultation': patient.motif_consultation,
                    'frequence_cardiaque': patient.constantes.frequence_cardiaque,
                    'pression_systolique': patient.constantes.pression_systolique,
                    'pression_diastolique': patient.constantes.pression_diastolique,
                    'frequence_respiratoire': patient.constantes.frequence_respiratoire,
                    'temperature': patient.constantes.temperature,
                    'saturation_oxygene': patient.constantes.saturation_oxygene,
                    'echelle_douleur': patient.constantes.echelle_douleur
                    # PAS DE GLYCEMIE !
                }
                
                df = pd.DataFrame([features])
                y_pred, y_proba, _ = self._classifier.predict(df)
                ml_prediction = y_pred[0]
                ml_score = float(np.max(y_proba[0]))

        except Exception as e:
            print(f"Erreur ML: {e}")

        # 3. CONSOLIDATION
        confidence = 0.75
        if ml_prediction and ml_prediction == french_result["gravity_level"]:
            confidence += 0.15
        if len(french_result["red_flags"]) > 0:
            confidence = 0.95

        justif = f"Niveau {french_result['french_triage_level']}."
        if french_result['red_flags']: justif += f" Alertes: {french_result['red_flags']}."
        
        # --- CALCUL FINAL DU TEMPS ---
        duration_ms = (time.time() - start_time) * 1000

        final_response = {
            "gravity_level": french_result["gravity_level"],
            "french_triage_level": french_result["french_triage_level"],
            "confidence_score": min(confidence, 0.99),
            "justification": justif,
            "red_flags": french_result["red_flags"],
            "recommendations": french_result["recommendations"],
            "orientation": french_result["orientation"],
            "delai_prise_en_charge": french_result["delai_prise_en_charge"],
            "model_version": self.model_version,
            "ml_score": ml_score,
            "processing_time_ms": duration_ms # <--- C'EST LUI QUI MANQUAIT
        }
        
        self._save_to_history(final_response)
        return final_response

# Instance
_service = TriageService()
def get_triage_service():
    return _service