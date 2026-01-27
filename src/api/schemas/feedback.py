"""
Schemas Pydantic pour le feedback des infirmieres.

Permet de collecter les corrections et d'ameliorer le modele.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Type de feedback sur une prediction."""
    CORRECT = "correct"       # La prediction etait correcte
    UPGRADE = "upgrade"       # Devrait etre plus grave (ex: VERT -> JAUNE)
    DOWNGRADE = "downgrade"   # Devrait etre moins grave (ex: JAUNE -> VERT)
    DISAGREE = "disagree"     # Completement en desaccord


class NurseFeedback(BaseModel):
    """Feedback d'une infirmiere sur une prediction de triage."""

    # Identifiant de la prediction originale
    prediction_id: str = Field(..., description="ID de la prediction a corriger")

    # Informations infirmiere (anonymisees)
    nurse_id: Optional[str] = Field(None, description="Identifiant anonyme de l'infirmiere")

    # Prediction originale
    original_gravity: str = Field(..., description="Niveau de gravite predit (GRIS/VERT/JAUNE/ROUGE)")
    original_french_level: Optional[str] = Field(None, description="Niveau FRENCH predit")

    # Correction
    feedback_type: FeedbackType = Field(..., description="Type de correction")
    corrected_gravity: Optional[str] = Field(
        None,
        description="Niveau de gravite corrige (si different)"
    )
    corrected_french_level: Optional[str] = Field(
        None,
        description="Niveau FRENCH corrige (si different)"
    )

    # Contexte
    reason: Optional[str] = Field(None, description="Raison de la correction")
    missed_symptoms: Optional[List[str]] = Field(
        default_factory=list,
        description="Symptomes manques par le systeme"
    )

    # Donnees patient pour reentrainement
    patient_features: Dict[str, Any] = Field(
        ...,
        description="Features du patient (pour reentrainement)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": "abc123",
                "nurse_id": "nurse_42",
                "original_gravity": "VERT",
                "original_french_level": "Tri 4",
                "feedback_type": "upgrade",
                "corrected_gravity": "JAUNE",
                "corrected_french_level": "Tri 3B",
                "reason": "Patient presente des signes de detresse respiratoire",
                "missed_symptoms": ["dyspnee", "tirage intercostal"],
                "patient_features": {
                    "age": 65,
                    "sexe": "M",
                    "frequence_cardiaque": 95,
                    "saturation_oxygene": 92,
                    "temperature": 38.5
                }
            }
        }


class FeedbackResponse(BaseModel):
    """Reponse apres soumission d'un feedback."""
    status: str = "recorded"
    feedback_id: str
    message: str = "Feedback enregistre avec succes"


class FeedbackStats(BaseModel):
    """Statistiques agregees des feedbacks."""

    # Compteurs globaux
    total_predictions: int = Field(0, description="Nombre total de predictions")
    total_feedback: int = Field(0, description="Nombre de feedbacks recus")

    # Taux
    accuracy_rate: float = Field(0.0, description="Taux de predictions correctes")
    upgrade_rate: float = Field(0.0, description="Taux de sous-estimation (upgrade)")
    downgrade_rate: float = Field(0.0, description="Taux de sur-estimation (downgrade)")
    disagree_rate: float = Field(0.0, description="Taux de desaccord total")

    # Par niveau de gravite
    by_gravity_level: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Stats par niveau de gravite"
    )

    # Periode
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class RetrainRequest(BaseModel):
    """Requete pour declencher un reentrainement."""
    include_feedback: bool = Field(
        True,
        description="Inclure les donnees de feedback dans l'entrainement"
    )
    min_feedback_samples: int = Field(
        50,
        description="Nombre minimum de feedbacks requis"
    )
    run_name: Optional[str] = Field(
        None,
        description="Nom du run MLflow"
    )


class RetrainResponse(BaseModel):
    """Reponse apres declenchement d'un reentrainement."""
    status: str
    mlflow_run_id: Optional[str] = None
    message: str
    feedback_samples_used: int = 0
