"""
Route Health Check
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from src.api.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Vérifie l'état de santé de l'API
    """
    # Test connexion DB
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status,
        },
        "version": "2.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """
    Vérifie si l'API est prête à recevoir du trafic
    """
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Vérifie si l'API est vivante
    """
    return {"alive": True}
