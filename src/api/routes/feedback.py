"""
Routes pour le feedback infirmier
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from src.api.core.database import get_db, TriagePrediction
from src.api.schemas.feedback import FeedbackInput, FeedbackResponse, FeedbackStats

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackInput,
    db: Session = Depends(get_db)
):
    """
    Soumet la validation infirmière d'une prédiction

    Cette validation est utilisée pour :
    - Améliorer le modèle via réentraînement
    - Calculer les métriques de performance
    - Identifier les cas où le modèle se trompe
    """
    # Récupérer la prédiction
    prediction = db.query(TriagePrediction).filter(
        TriagePrediction.id == feedback.prediction_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")

    if prediction.validated:
        raise HTTPException(status_code=400, detail="Cette prédiction a déjà été validée")

    # Mettre à jour avec le feedback
    original_level = prediction.predicted_level
    prediction.validated = True
    prediction.validated_at = datetime.utcnow()
    prediction.validated_level = feedback.validated_level.value
    prediction.validator_notes = feedback.notes

    db.commit()

    # Compter les feedbacks du jour
    today = datetime.utcnow().date()
    feedback_count = db.query(TriagePrediction).filter(
        TriagePrediction.validated == True,
        func.date(TriagePrediction.validated_at) == today
    ).count()

    return FeedbackResponse(
        success=True,
        message="Feedback enregistré avec succès",
        prediction_id=feedback.prediction_id,
        original_level=original_level,
        validated_level=feedback.validated_level.value,
        feedback_count_today=feedback_count
    )


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques des feedbacks

    - **days**: Nombre de jours à analyser (défaut: 30)
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total prédictions
    total_predictions = db.query(TriagePrediction).filter(
        TriagePrediction.created_at >= start_date
    ).count()

    # Total validées
    total_validated = db.query(TriagePrediction).filter(
        TriagePrediction.created_at >= start_date,
        TriagePrediction.validated == True
    ).count()

    # Calcul précision (prédictions correctes)
    correct_predictions = db.query(TriagePrediction).filter(
        TriagePrediction.created_at >= start_date,
        TriagePrediction.validated == True,
        TriagePrediction.predicted_level == TriagePrediction.validated_level
    ).count()

    accuracy_rate = correct_predictions / total_validated if total_validated > 0 else 0

    # Stats par niveau
    stats_by_level = {}
    for level in ["ROUGE", "JAUNE", "VERT", "GRIS"]:
        predicted = db.query(TriagePrediction).filter(
            TriagePrediction.created_at >= start_date,
            TriagePrediction.predicted_level == level
        ).count()

        validated_correct = db.query(TriagePrediction).filter(
            TriagePrediction.created_at >= start_date,
            TriagePrediction.predicted_level == level,
            TriagePrediction.validated == True,
            TriagePrediction.validated_level == level
        ).count()

        validated_total = db.query(TriagePrediction).filter(
            TriagePrediction.created_at >= start_date,
            TriagePrediction.predicted_level == level,
            TriagePrediction.validated == True
        ).count()

        stats_by_level[level] = {
            "predicted_count": predicted,
            "validated_count": validated_total,
            "accuracy": validated_correct / validated_total if validated_total > 0 else None
        }

    # Matrice de confusion simplifiée
    confusion_matrix = {}
    levels = ["ROUGE", "JAUNE", "VERT", "GRIS"]

    for pred_level in levels:
        confusion_matrix[pred_level] = {}
        for val_level in levels:
            count = db.query(TriagePrediction).filter(
                TriagePrediction.created_at >= start_date,
                TriagePrediction.validated == True,
                TriagePrediction.predicted_level == pred_level,
                TriagePrediction.validated_level == val_level
            ).count()
            confusion_matrix[pred_level][val_level] = count

    return FeedbackStats(
        total_predictions=total_predictions,
        total_validated=total_validated,
        validation_rate=total_validated / total_predictions if total_predictions > 0 else 0,
        accuracy_rate=accuracy_rate,
        stats_by_level=stats_by_level,
        confusion_matrix=confusion_matrix,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/feedback/pending")
async def get_pending_validations(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Récupère les prédictions en attente de validation
    """
    predictions = db.query(TriagePrediction).filter(
        TriagePrediction.validated == False
    ).order_by(
        TriagePrediction.created_at.desc()
    ).limit(limit).all()

    return {
        "pending_predictions": predictions,
        "count": len(predictions)
    }


@router.get("/feedback/export")
async def export_feedback_data(
    format: str = "json",
    days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Exporte les données de feedback pour réentraînement

    - **format**: Format d'export (json, csv)
    - **days**: Limiter aux N derniers jours (optionnel)
    """
    query = db.query(TriagePrediction).filter(
        TriagePrediction.validated == True
    )

    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(TriagePrediction.created_at >= start_date)

    predictions = query.all()

    # Formater pour l'export
    data = []
    for p in predictions:
        data.append({
            "age": p.patient_age,
            "sexe": p.patient_sexe,
            "motif_consultation": p.motif_consultation,
            "frequence_cardiaque": p.frequence_cardiaque,
            "frequence_respiratoire": p.frequence_respiratoire,
            "saturation_oxygene": p.saturation_oxygene,
            "pression_systolique": p.pression_systolique,
            "pression_diastolique": p.pression_diastolique,
            "temperature": p.temperature,
            "echelle_douleur": p.echelle_douleur,
            "gravity_level": p.validated_level,  # Utiliser le niveau validé comme label
            "french_triage_level": p.french_triage_level,
            "original_prediction": p.predicted_level,
            "was_correct": p.predicted_level == p.validated_level
        })

    return {
        "format": format,
        "count": len(data),
        "data": data
    }
