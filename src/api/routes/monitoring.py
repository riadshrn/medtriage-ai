from fastapi import APIRouter, status
from src.api.schemas.monitoring import LLMMetrics
from src.api.services.monitoring_service import get_monitoring_service

router = APIRouter()

@router.post("/log", status_code=status.HTTP_201_CREATED)
async def log_interaction(metric: LLMMetrics):
    """
    Endpoint technique appelé par le pipeline RAG pour archiver
    les métriques de coût et de carbone après une génération.
    """
    service = get_monitoring_service()
    service.log_metric(metric)
    return {"status": "logged"}

@router.get("/history")
async def get_history():
    """Pour alimenter le dashboard"""
    service = get_monitoring_service()
    return service.get_stats()