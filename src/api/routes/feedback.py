"""
Routes API pour le feedback des infirmieres.

Endpoints:
- POST /feedback/submit : Soumettre un feedback
- GET /feedback/stats : Obtenir les statistiques
- POST /feedback/retrain : Declencher un reentrainement manuel
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.feedback import (
    NurseFeedback,
    FeedbackResponse,
    FeedbackStats,
    RetrainRequest,
    RetrainResponse,
)
from src.api.ml.feedback_handler import get_feedback_handler
from src.api.ml.mlflow_config import MLflowConfig, MLFLOW_AVAILABLE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: NurseFeedback):
    """
    Soumet un feedback sur une prediction de triage.

    Le feedback est utilise pour:
    - Suivre la performance du modele
    - Reentrainer le modele avec les corrections

    Args:
        feedback: Feedback de l'infirmiere

    Returns:
        Confirmation de l'enregistrement
    """
    try:
        handler = get_feedback_handler()
        feedback_id = handler.record_feedback(feedback)

        return FeedbackResponse(
            status="recorded",
            feedback_id=feedback_id,
            message="Feedback enregistre avec succes. Merci pour votre contribution!"
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    since_days: Optional[int] = Query(
        None,
        description="Limiter aux N derniers jours"
    )
):
    """
    Retourne les statistiques agregees des feedbacks.

    Permet de suivre:
    - Le taux de predictions correctes
    - Les types d'erreurs (sous/sur-estimation)
    - La repartition par niveau de gravite
    """
    try:
        handler = get_feedback_handler()

        # Calculer la date de debut si specifie
        since = None
        if since_days is not None:
            from datetime import timedelta
            since = datetime.now() - timedelta(days=since_days)

        stats = handler.get_stats(since=since)
        return stats

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


@router.get("/count")
async def get_feedback_count():
    """Retourne le nombre total de feedbacks enregistres."""
    handler = get_feedback_handler()
    count = handler.get_feedback_count()
    return {"count": count}


@router.post("/retrain", response_model=RetrainResponse)
async def trigger_retraining(request: RetrainRequest):
    """
    Declenche un reentrainement manuel du modele.

    Le reentrainement:
    1. Charge les donnees originales
    2. Ajoute les corrections des feedbacks
    3. Entraine un nouveau modele
    4. L'enregistre dans MLflow

    Note: Cette operation peut prendre plusieurs minutes.
    """
    try:
        handler = get_feedback_handler()

        # Verifier qu'on a assez de feedbacks
        if request.include_feedback:
            feedback_df = handler.get_feedback_for_retraining(
                min_samples=request.min_feedback_samples
            )

            if feedback_df.empty:
                return RetrainResponse(
                    status="skipped",
                    message=f"Pas assez de feedbacks pour reentrainement "
                            f"(minimum: {request.min_feedback_samples})",
                    feedback_samples_used=0
                )

            feedback_count = len(feedback_df)
        else:
            feedback_count = 0

        # Lancer l'entrainement
        from src.api.ml.trainer import ModelTrainer
        import pandas as pd

        trainer = ModelTrainer()

        logger.info(f"MLflow enabled: {trainer._mlflow_enabled} | URI: {MLflowConfig.TRACKING_URI}")


        # Charger les donnees originales
        original_df = trainer.preprocessor.load_data("data/raw/patients_synthetic.csv")

        # Combiner avec feedback si demande
        if request.include_feedback and not feedback_df.empty:
            combined_df = pd.concat([original_df, feedback_df], ignore_index=True)
            logger.info(f"Donnees combinees: {len(original_df)} originales + {feedback_count} feedbacks")
        else:
            combined_df = original_df

        # Sauvegarder temporairement
        combined_path = "data/processed/combined_training.csv"
        from pathlib import Path
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(combined_path, index=False)

        # Entrainer
        run_name = request.run_name or f"retrain-feedback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        classifier = trainer.train_from_csv(
            csv_path=combined_path,
            run_name=run_name,
            tags={"trigger": "feedback", "feedback_samples": str(feedback_count)},
            register_model=True,
        )

        # Recuperer le run ID MLflow
        
        run_id = None
        if MLFLOW_AVAILABLE:
            import mlflow
            if mlflow.active_run():
                run_id = mlflow.active_run().info.run_id

        return RetrainResponse(
            status="completed",
            mlflow_run_id=run_id,
            message=f"Reentrainement termine avec succes. "
                    f"Modele enregistre dans MLflow.",
            feedback_samples_used=feedback_count
        )

    except Exception as e:
        logger.error(f"Erreur lors du reentrainement: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du reentrainement: {str(e)}"
        )
