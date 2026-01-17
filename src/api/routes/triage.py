"""
Routes pour le triage des patients
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.api.core.database import get_db, TriagePrediction
from src.api.core.config import settings
from src.api.schemas.triage import PatientInput, TriageResponse, GravityLevelEnum, FrenchTriageLevelEnum
from src.api.services.triage_service import TriageService

router = APIRouter()

# Service de triage (singleton)
_triage_service = None


def get_triage_service() -> TriageService:
    """Récupère ou initialise le service de triage"""
    global _triage_service
    if _triage_service is None:
        _triage_service = TriageService(
            ml_model_path=settings.ML_MODEL_PATH,
            ml_preprocessor_path=settings.ML_PREPROCESSOR_PATH,
            vector_store_path=settings.VECTOR_STORE_PATH
        )
    return _triage_service


@router.post("/triage", response_model=TriageResponse)
async def perform_triage(
    patient: PatientInput,
    use_rag: bool = True,
    db: Session = Depends(get_db)
):
    """
    Effectue le triage d'un patient

    - **patient**: Données du patient (âge, sexe, motif, constantes)
    - **use_rag**: Utiliser le RAG pour enrichir l'analyse (défaut: True)

    Retourne le niveau de gravité et les recommandations.
    """
    start_time = time.time()

    try:
        service = get_triage_service()
        result = service.triage(patient, use_rag=use_rag)

        processing_time = (time.time() - start_time) * 1000

        # Sauvegarder en base
        prediction = TriagePrediction(
            patient_age=patient.age,
            patient_sexe=patient.sexe,
            motif_consultation=patient.motif_consultation,
            frequence_cardiaque=patient.constantes.frequence_cardiaque,
            frequence_respiratoire=patient.constantes.frequence_respiratoire,
            saturation_oxygene=patient.constantes.saturation_oxygene,
            pression_systolique=patient.constantes.pression_systolique,
            pression_diastolique=patient.constantes.pression_diastolique,
            temperature=patient.constantes.temperature,
            echelle_douleur=patient.constantes.echelle_douleur,
            predicted_level=result["gravity_level"],
            french_triage_level=result["french_triage_level"],
            confidence_score=result["confidence_score"],
            ml_score=result["ml_score"],
            rag_context=result.get("rag_context"),
            model_version=result["model_version"],
            processing_time_ms=processing_time
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return TriageResponse(
            prediction_id=prediction.id,
            gravity_level=GravityLevelEnum(result["gravity_level"]),
            french_triage_level=FrenchTriageLevelEnum(result["french_triage_level"]),
            confidence_score=result["confidence_score"],
            ml_score=result["ml_score"],
            delai_prise_en_charge=result["delai_prise_en_charge"],
            orientation=result["orientation"],
            justification=result["justification"],
            red_flags=result.get("red_flags", []),
            recommendations=result.get("recommendations", []),
            model_version=result["model_version"],
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de triage: {str(e)}")


@router.get("/triage/{prediction_id}")
async def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'une prédiction
    """
    prediction = db.query(TriagePrediction).filter(
        TriagePrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")

    return prediction


@router.get("/triage/history/recent")
async def get_recent_predictions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Récupère les prédictions récentes
    """
    predictions = db.query(TriagePrediction).order_by(
        TriagePrediction.created_at.desc()
    ).limit(limit).all()

    return {
        "predictions": predictions,
        "count": len(predictions)
    }
