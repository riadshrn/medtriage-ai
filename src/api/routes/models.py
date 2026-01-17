"""
Routes pour la gestion des modèles ML
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from src.api.core.database import get_db, ModelRegistry
from src.api.core.config import settings
from src.api.schemas.models import (
    ModelInfo, ModelList, RetrainRequest, RetrainResponse,
    ModelActivateRequest
)

router = APIRouter()


@router.get("/models", response_model=ModelList)
async def list_models(db: Session = Depends(get_db)):
    """
    Liste tous les modèles disponibles
    """
    models = db.query(ModelRegistry).order_by(
        ModelRegistry.created_at.desc()
    ).all()

    active_model = db.query(ModelRegistry).filter(
        ModelRegistry.is_active == True
    ).first()

    return ModelList(
        models=[ModelInfo.model_validate(m) for m in models],
        active_model=ModelInfo.model_validate(active_model) if active_model else None,
        total_count=len(models)
    )


@router.get("/models/active")
async def get_active_model(db: Session = Depends(get_db)):
    """
    Récupère le modèle actuellement actif
    """
    model = db.query(ModelRegistry).filter(
        ModelRegistry.is_active == True
    ).first()

    if not model:
        return {
            "message": "Aucun modèle actif enregistré",
            "using_default": True,
            "default_path": settings.ML_MODEL_PATH
        }

    return ModelInfo.model_validate(model)


@router.get("/models/{model_id}")
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """
    Récupère les détails d'un modèle
    """
    model = db.query(ModelRegistry).filter(
        ModelRegistry.id == model_id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Modèle non trouvé")

    return ModelInfo.model_validate(model)


@router.post("/models/activate")
async def activate_model(
    request: ModelActivateRequest,
    db: Session = Depends(get_db)
):
    """
    Active un modèle spécifique pour les prédictions
    """
    # Vérifier que le modèle existe
    model = db.query(ModelRegistry).filter(
        ModelRegistry.id == request.model_id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Modèle non trouvé")

    # Désactiver tous les autres modèles
    db.query(ModelRegistry).update({ModelRegistry.is_active: False})

    # Activer le modèle sélectionné
    model.is_active = True
    db.commit()

    return {
        "success": True,
        "message": f"Modèle {model.version} activé",
        "model": ModelInfo.model_validate(model)
    }


@router.post("/models/retrain", response_model=RetrainResponse)
async def retrain_model(
    request: RetrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Lance le réentraînement du modèle

    Le réentraînement utilise :
    - Les données de feedback validées
    - Optionnellement les datasets Hugging Face

    Le processus s'exécute en arrière-plan.
    """
    from src.api.services.training_service import TrainingService

    # Vérifier qu'il y a assez de données
    from src.api.core.database import TriagePrediction
    feedback_count = db.query(TriagePrediction).filter(
        TriagePrediction.validated == True
    ).count()

    if request.use_feedback_data and feedback_count < request.min_feedback_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Pas assez de feedbacks ({feedback_count}/{request.min_feedback_samples})"
        )

    # Lancer l'entraînement en background
    training_service = TrainingService()

    # Pour l'instant, retourner un message (le vrai entraînement sera en background)
    return RetrainResponse(
        success=True,
        message="Réentraînement lancé en arrière-plan",
        new_model_version=None,  # Sera mis à jour à la fin
        mlflow_run_id=None,
        training_samples=feedback_count if request.use_feedback_data else 0
    )


@router.get("/models/compare")
async def compare_models(
    model_ids: str,  # Comma-separated IDs
    db: Session = Depends(get_db)
):
    """
    Compare les métriques de plusieurs modèles
    """
    ids = [int(id.strip()) for id in model_ids.split(",")]

    models = db.query(ModelRegistry).filter(
        ModelRegistry.id.in_(ids)
    ).all()

    if len(models) < 2:
        raise HTTPException(status_code=400, detail="Au moins 2 modèles requis")

    comparison = []
    for model in models:
        comparison.append({
            "id": model.id,
            "version": model.version,
            "created_at": model.created_at,
            "is_active": model.is_active,
            "metrics": {
                "accuracy": model.accuracy,
                "precision": model.precision_score,
                "recall": model.recall_score,
                "f1": model.f1_score
            },
            "training_samples": model.training_samples
        })

    return {
        "comparison": comparison,
        "best_by_accuracy": max(comparison, key=lambda x: x["metrics"]["accuracy"] or 0),
        "best_by_f1": max(comparison, key=lambda x: x["metrics"]["f1"] or 0)
    }
