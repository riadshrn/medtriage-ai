from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from api.schemas.triage import PatientInput, TriageResponse, ConstantesInput
from api.services.triage_service import get_triage_service

router = APIRouter()


@router.post("/predict", response_model=TriageResponse)
async def predict_triage(patient: PatientInput):
    """Endpoint de Triage Intelligent."""
    try:
        service = get_triage_service()
        result = service.predict(patient)
        return TriageResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_from_extraction(extracted_data: Dict[str, Any]) -> Dict:
    """
    Évalue le triage à partir des données extraites d'une conversation.

    Utilisé par le mode simulation pour évaluer le triage
    basé sur les informations collectées pendant l'entretien.
    """
    try:
        constantes_data = extracted_data.get("constantes") or {}

        patient = PatientInput(
            age=extracted_data.get("age") or 45,
            sexe=extracted_data.get("sexe") or "M",
            motif_consultation=extracted_data.get("motif_consultation") or "Non spécifié",
            antecedents=extracted_data.get("antecedents") or [],
            constantes=ConstantesInput(
                frequence_cardiaque=constantes_data.get("frequence_cardiaque") or 80,
                pression_systolique=constantes_data.get("pression_systolique") or 120,
                pression_diastolique=constantes_data.get("pression_diastolique") or 80,
                frequence_respiratoire=constantes_data.get("frequence_respiratoire") or 16,
                temperature=constantes_data.get("temperature") or 37.0,
                saturation_oxygene=constantes_data.get("saturation_oxygene") or 98,
                echelle_douleur=constantes_data.get("echelle_douleur") or 0,
                glycemie=constantes_data.get("glycemie"),
                glasgow=constantes_data.get("glasgow") or 15,
            )
        )

        service = get_triage_service()
        return service.predict(patient)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))