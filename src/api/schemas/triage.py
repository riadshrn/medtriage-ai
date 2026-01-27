from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class GravityLevelEnum(str, Enum):
    ROUGE = "ROUGE"
    JAUNE = "JAUNE"
    VERT = "VERT"
    GRIS = "GRIS"

class FrenchTriageLevelEnum(str, Enum):
    TRI_1 = "Tri 1"
    TRI_2 = "Tri 2"
    TRI_3A = "Tri 3A"
    TRI_3B = "Tri 3B"
    TRI_4 = "Tri 4"
    TRI_5 = "Tri 5"

class ConstantesInput(BaseModel):
    frequence_cardiaque: int = Field(..., ge=0, le=300)
    pression_systolique: int = Field(..., ge=0, le=300)
    pression_diastolique: int = Field(..., ge=0, le=200)
    frequence_respiratoire: int = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=20.0, le=45.0)
    saturation_oxygene: int = Field(..., ge=0, le=100)
    echelle_douleur: int = Field(0, ge=0, le=10)
    # AJOUT ESSENTIEL POUR LE FIX :
    glycemie: Optional[float] = None 
    glasgow: Optional[int] = 15

class PatientInput(BaseModel):
    age: int = Field(..., ge=0, le=120)
    sexe: str = Field(..., pattern="^(M|F)$")
    motif_consultation: str
    constantes: ConstantesInput
    antecedents: Optional[List[str]] = []

class PredictionQualityEnum(str, Enum):
    """Niveau de qualite des donnees pour la prediction ML."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class TriageResponse(BaseModel):
    """Reponse du service de triage."""
    # Identifiant unique de la prediction (pour feedback)
    prediction_id: Optional[str] = None

    # Resultat principal
    gravity_level: GravityLevelEnum
    french_triage_level: FrenchTriageLevelEnum
    confidence_score: float
    justification: str

    # Details cliniques
    red_flags: List[str] = []
    recommendations: List[str] = []
    orientation: str
    delai_prise_en_charge: str

    # Metadata
    processing_time_ms: float
    model_version: str

    # Informations ML
    ml_score: Optional[float] = 0.0
    ml_available: Optional[bool] = True
    ml_error: Optional[str] = None

    # Qualite des donnees
    prediction_quality: Optional[PredictionQualityEnum] = PredictionQualityEnum.HIGH
    missing_features: Optional[List[str]] = []