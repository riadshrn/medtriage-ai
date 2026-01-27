from typing import Dict

from fastapi import APIRouter, HTTPException
import time
from src.api.schemas.triage import ConstantesInput, PatientInput, TriageResponse
from src.api.services.triage_service import get_triage_service

router = APIRouter()

@router.post("/predict", response_model=TriageResponse)
async def predict_triage(patient: PatientInput):
    """
    Endpoint de Triage Intelligent.
    """
    start_time = time.time()
    try:
        service = get_triage_service()
        result = service.predict(patient)
        
        duration = (time.time() - start_time) * 1000
        
        # Construction de la réponse typée
        return TriageResponse(
            **result, # Unpack du dict du service
            processing_time_ms=duration
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_triage(data: Dict) -> Dict:
    """
    Évalue le niveau de triage à partir de données extraites.

    Endpoint adapté pour recevoir les données issues de l'extraction
    automatique de conversation. Convertit les données brutes en
    format PatientInput avant évaluation.

    Args:
        data: Dictionnaire contenant les données extraites (age, sexe, constantes, etc.)

    Returns:
        Résultat du triage avec niveau FRENCH et recommandations
    """
    try:
        constantes_data = data.get("constantes", {}) or {}

        constantes = ConstantesInput(
            frequence_cardiaque=constantes_data.get("frequence_cardiaque") or 80,
            pression_systolique=constantes_data.get("pression_systolique") or 120,
            pression_diastolique=constantes_data.get("pression_diastolique") or 80,
            frequence_respiratoire=constantes_data.get("frequence_respiratoire") or 16,
            temperature=constantes_data.get("temperature") or 37.0,
            saturation_oxygene=constantes_data.get("saturation_oxygene") or 98,
            echelle_douleur=constantes_data.get("echelle_douleur") or 0,
            glycemie=constantes_data.get("glycemie"),
            glasgow=constantes_data.get("glasgow") or 15
        )

        patient = PatientInput(
            age=data.get("age") or 45,
            sexe=data.get("sexe") or "M",
            motif_consultation=data.get("motif_consultation") or "Non spécifié",
            constantes=constantes,
            antecedents=data.get("antecedents") or []
        )

        service = get_triage_service()
        result = service.predict(patient)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))