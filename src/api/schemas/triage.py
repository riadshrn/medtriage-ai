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

class TriageResponse(BaseModel):
    gravity_level: GravityLevelEnum
    french_triage_level: FrenchTriageLevelEnum
    confidence_score: float
    justification: str
    red_flags: List[str] = []
    recommendations: List[str] = []
    orientation: str
    delai_prise_en_charge: str
    processing_time_ms: float
    model_version: str
    # Debug infos
    ml_score: Optional[float] = 0.0