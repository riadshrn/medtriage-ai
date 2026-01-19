"""
Schémas Pydantic pour la gestion des modèles
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ModelInfo(BaseModel):
    """Information sur un modèle"""
    id: int
    model_name: str
    version: str
    created_at: datetime
    is_active: bool

    # Métriques
    accuracy: Optional[float]
    precision_score: Optional[float]
    recall_score: Optional[float]
    f1_score: Optional[float]

    # Détails
    training_samples: Optional[int]
    mlflow_run_id: Optional[str]

    class Config:
        from_attributes = True


class ModelList(BaseModel):
    """Liste des modèles disponibles"""
    models: List[ModelInfo]
    active_model: Optional[ModelInfo]
    total_count: int


class RetrainRequest(BaseModel):
    """Demande de réentraînement"""
    use_feedback_data: bool = Field(
        default=True,
        description="Utiliser les données de feedback validées"
    )
    use_hf_datasets: bool = Field(
        default=False,
        description="Inclure les datasets Hugging Face"
    )
    min_feedback_samples: int = Field(
        default=10,
        ge=5,
        description="Nombre minimum de feedbacks pour réentraîner"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hyperparamètres personnalisés"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "use_feedback_data": True,
                "use_hf_datasets": True,
                "min_feedback_samples": 100,
                "hyperparameters": {
                    "n_estimators": 200,
                    "max_depth": 10,
                    "learning_rate": 0.1
                }
            }
        }


class RetrainResponse(BaseModel):
    """Réponse après réentraînement"""
    success: bool
    message: str
    new_model_version: Optional[str]
    mlflow_run_id: Optional[str]

    # Métriques du nouveau modèle
    metrics: Optional[Dict[str, float]] = Field(
        default=None,
        description="Métriques d'évaluation"
    )

    # Comparaison
    improvement: Optional[Dict[str, float]] = Field(
        default=None,
        description="Amélioration par rapport au modèle précédent"
    )

    training_samples: Optional[int]
    training_duration_seconds: Optional[float]


class ModelActivateRequest(BaseModel):
    """Demande d'activation d'un modèle"""
    model_id: int = Field(..., description="ID du modèle à activer")


class ModelCompareRequest(BaseModel):
    """Demande de comparaison de modèles"""
    model_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="IDs des modèles à comparer"
    )
