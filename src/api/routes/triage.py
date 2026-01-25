from fastapi import APIRouter, HTTPException
import time
from src.api.schemas.triage import PatientInput, TriageResponse
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