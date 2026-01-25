import sys
from pathlib import Path
from typing import Optional
import time
import pandas as pd
import numpy as np

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
        
        # --- FIX 1 : On définit la version ici ---
        self.model_version = "v2.0.0-hybrid"

    def _load_ml_model(self):
        """Lazy loading via le wrapper legacy"""
        if self._classifier is None:
            try:
                self._classifier = TriageClassifier.load(
                    model_path=self.ml_model_path,
                    preprocessor_path=self.ml_preprocessor_path
                )
                print(f"✅ Modèle ML chargé via TriageClassifier")
            except Exception as e:
                print(f"⚠️ Erreur chargement ML : {e}")

    def predict(self, patient: PatientInput) -> dict:
        """
        Pipeline: 1. FRENCH -> 2. ML (si dispo) -> 3. Fusion
        """
        # 1. ÉVALUATION FRENCH
        # On map le schéma Pydantic vers la dataclass du moteur
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

        # 2. PRÉDICTION ML
        ml_score = 0.5
        ml_prediction = None
        
        try:
            self._load_ml_model()
            if self._classifier:
                # --- FIX 2 : Accès sécurisé à la glycémie ---
                # On utilise getattr pour éviter le crash si le champ manque
                glycemie_val = getattr(patient.constantes, 'glycemie', None)
                
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
                    'echelle_douleur': patient.constantes.echelle_douleur,
                    'glycemie': glycemie_val  # Passé de manière sûre
                }
                
                df = pd.DataFrame([features])
                y_pred, y_proba, _ = self._classifier.predict(df)
                
                ml_prediction = y_pred[0]
                ml_score = float(np.max(y_proba[0]))

        except Exception as e:
            print(f"Erreur ML: {e}") 
            # On continue même si le ML plante (Graceful degradation)

        # 3. CONSOLIDATION
        confidence = self._calculate_confidence(french_result, ml_score, ml_prediction)
        justif = self._build_justification(french_result, ml_prediction)

        return {
            "gravity_level": french_result["gravity_level"],
            "french_triage_level": french_result["french_triage_level"],
            "confidence_score": confidence,
            "justification": justif,
            "red_flags": french_result["red_flags"],
            "recommendations": french_result["recommendations"],
            "orientation": french_result["orientation"],
            "delai_prise_en_charge": french_result["delai_prise_en_charge"],
            "model_version": self.model_version, # Maintenant ça existe !
            "ml_score": ml_score
        }

    def _calculate_confidence(self, french_res, ml_score, ml_pred):
        conf = 0.75
        if ml_pred and ml_pred == french_res["gravity_level"]:
            conf += 0.15
        if len(french_res["red_flags"]) > 0:
            conf = 0.95
        return min(conf, 0.99)

    def _build_justification(self, french_res, ml_pred):
        text = f"Niveau {french_res['french_triage_level']} déterminé par protocole."
        if french_res['red_flags']:
            text += f" Alertes: {', '.join(french_res['red_flags'])}."
        if ml_pred:
            accord = "confirme" if ml_pred == french_res['gravity_level'] else f"suggère {ml_pred}"
            text += f" (IA {accord})"
        return text

# Instance unique
_service = TriageService()
def get_triage_service():
    return _service