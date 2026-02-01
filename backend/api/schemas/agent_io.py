from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from api.schemas.extraction import ExtractedPatient
from api.schemas.validators import validate_medical_relevance # <-- Import

class AgentResponse(BaseModel):
    """
    Structure de réponse atomique pour l'Agent de Régulation.
    """
    
    criticity: Literal["ROUGE", "JAUNE", "VERT", "GRIS"] = Field(
        ...,
        description="Niveau de gravité trié..."
    )

    missing_info: List[str] = Field(
        default_factory=list,
        description="Liste des questions CRITIQUES..."
    )
    
    protocol_alert: Optional[str] = Field(
        None, 
        description="Alerte basée sur les protocoles médicaux..."
    )
    
    data: ExtractedPatient = Field(
        ..., 
        description="L'extraction structurée stricte des données du patient."
    )

    @field_validator('protocol_alert')
    @classmethod
    def check_alert_relevance(cls, v: str) -> str:
        if v:
            return validate_medical_relevance(v)
        return v

    @field_validator('missing_info')
    @classmethod
    def check_questions_relevance(cls, v: List[str]) -> List[str]:
        return [validate_medical_relevance(q) for q in v]