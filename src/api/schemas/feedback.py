"""
Schémas Pydantic pour le feedback infirmier
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from src.api.schemas.triage import GravityLevelEnum


class FeedbackInput(BaseModel):
    """Validation infirmière d'une prédiction"""
    prediction_id: int = Field(..., description="ID de la prédiction à valider")
    validated_level: GravityLevelEnum = Field(..., description="Niveau corrigé par l'infirmière")
    is_correct: bool = Field(..., description="La prédiction était-elle correcte ?")
    notes: Optional[str] = Field(None, max_length=1000, description="Commentaires de l'infirmière")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": 123,
                "validated_level": "JAUNE",
                "is_correct": False,
                "notes": "Patient avec antécédents cardiaques, niveau JAUNE plus approprié"
            }
        }


class FeedbackResponse(BaseModel):
    """Réponse après validation"""
    success: bool
    message: str
    prediction_id: int
    original_level: str
    validated_level: str
    feedback_count_today: int = Field(..., description="Nombre de feedbacks aujourd'hui")


class FeedbackStats(BaseModel):
    """Statistiques des feedbacks"""
    total_predictions: int
    total_validated: int
    validation_rate: float = Field(..., ge=0, le=1)
    accuracy_rate: float = Field(..., ge=0, le=1, description="% de prédictions correctes")

    # Par niveau
    stats_by_level: dict = Field(
        ...,
        description="Stats par niveau de gravité"
    )

    # Tendances
    confusion_matrix: dict = Field(
        ...,
        description="Matrice de confusion prédiction vs validation"
    )

    # Période
    period_start: datetime
    period_end: datetime


class FeedbackListItem(BaseModel):
    """Item de la liste des feedbacks"""
    prediction_id: int
    created_at: datetime
    validated_at: datetime
    patient_age: int
    motif_consultation: str
    predicted_level: str
    validated_level: str
    is_correct: bool
    notes: Optional[str]

    class Config:
        from_attributes = True
