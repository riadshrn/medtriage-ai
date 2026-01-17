"""
Schémas Pydantic pour le triage
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GravityLevelEnum(str, Enum):
    """Niveaux de gravité (mapping FRENCH -> 4 niveaux)"""
    ROUGE = "ROUGE"   # Tri 1, Tri 2
    JAUNE = "JAUNE"   # Tri 3A, Tri 3B
    VERT = "VERT"     # Tri 4
    GRIS = "GRIS"     # Tri 5


class FrenchTriageLevelEnum(str, Enum):
    """Niveaux FRENCH officiels"""
    TRI_1 = "Tri 1"   # Détresse vitale majeure
    TRI_2 = "Tri 2"   # Atteinte patente d'un organe
    TRI_3A = "Tri 3A" # Atteinte potentielle, comorbidités
    TRI_3B = "Tri 3B" # Atteinte potentielle, sans comorbidités
    TRI_4 = "Tri 4"   # Atteinte fonctionnelle stable
    TRI_5 = "Tri 5"   # Pas d'atteinte évidente


class ConstantesInput(BaseModel):
    """Constantes vitales du patient"""
    frequence_cardiaque: int = Field(..., ge=20, le=250, description="FC en bpm")
    frequence_respiratoire: int = Field(..., ge=5, le=60, description="FR en cycles/min")
    saturation_oxygene: float = Field(..., ge=50, le=100, description="SpO2 en %")
    pression_systolique: int = Field(..., ge=40, le=250, description="PAS en mmHg")
    pression_diastolique: int = Field(..., ge=20, le=150, description="PAD en mmHg")
    temperature: float = Field(..., ge=32, le=43, description="Température en °C")
    echelle_douleur: int = Field(..., ge=0, le=10, description="EVA 0-10")

    class Config:
        json_schema_extra = {
            "example": {
                "frequence_cardiaque": 85,
                "frequence_respiratoire": 16,
                "saturation_oxygene": 98,
                "pression_systolique": 120,
                "pression_diastolique": 80,
                "temperature": 37.2,
                "echelle_douleur": 3
            }
        }


class PatientInput(BaseModel):
    """Données patient pour le triage"""
    age: int = Field(..., ge=0, le=120, description="Âge du patient")
    sexe: str = Field(..., pattern="^[MF]$", description="Sexe (M/F)")
    motif_consultation: str = Field(..., min_length=3, max_length=1000, description="Motif de consultation")
    constantes: ConstantesInput
    antecedents: Optional[List[str]] = Field(default=None, description="Antécédents médicaux")
    allergies: Optional[List[str]] = Field(default=None, description="Allergies connues")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 45,
                "sexe": "M",
                "motif_consultation": "Douleur thoracique intense depuis 30 minutes",
                "constantes": {
                    "frequence_cardiaque": 110,
                    "frequence_respiratoire": 22,
                    "saturation_oxygene": 94,
                    "pression_systolique": 160,
                    "pression_diastolique": 95,
                    "temperature": 36.8,
                    "echelle_douleur": 8
                },
                "antecedents": ["HTA", "Diabète type 2"],
                "allergies": ["Pénicilline"]
            }
        }


class TriageResponse(BaseModel):
    """Réponse du triage"""
    prediction_id: int = Field(..., description="ID de la prédiction pour le feedback")

    # Classification
    gravity_level: GravityLevelEnum = Field(..., description="Niveau de gravité (4 niveaux)")
    french_triage_level: FrenchTriageLevelEnum = Field(..., description="Niveau FRENCH officiel")

    # Scores
    confidence_score: float = Field(..., ge=0, le=1, description="Score de confiance global")
    ml_score: float = Field(..., ge=0, le=1, description="Score du modèle ML")

    # Détails
    delai_prise_en_charge: str = Field(..., description="Délai maximal recommandé")
    orientation: str = Field(..., description="Orientation recommandée")
    justification: str = Field(..., description="Justification de la classification")

    # Alertes
    red_flags: List[str] = Field(default=[], description="Signaux d'alerte identifiés")
    recommendations: List[str] = Field(default=[], description="Actions recommandées")

    # Métadonnées
    model_version: str
    processing_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": 123,
                "gravity_level": "ROUGE",
                "french_triage_level": "Tri 2",
                "confidence_score": 0.92,
                "ml_score": 0.88,
                "delai_prise_en_charge": "< 20 minutes",
                "orientation": "SAUV ou Box",
                "justification": "Douleur thoracique avec facteurs de risque cardiovasculaires",
                "red_flags": ["Douleur thoracique", "HTA", "Diabète"],
                "recommendations": [
                    "ECG immédiat",
                    "Monitoring cardiaque",
                    "Voie veineuse"
                ],
                "model_version": "v2.0.0-20260117",
                "processing_time_ms": 45.2
            }
        }


class TriagePredictionDB(BaseModel):
    """Prédiction stockée en base"""
    id: int
    created_at: datetime
    patient_age: int
    patient_sexe: str
    motif_consultation: str
    predicted_level: str
    french_triage_level: str
    confidence_score: float
    validated: bool
    validated_level: Optional[str]

    class Config:
        from_attributes = True
