from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas.extraction import ExtractedPatient

class AgentResponse(BaseModel):
    """
    Structure de réponse atomique pour l'Agent de Régulation.
    Permet un affichage modulaire dans le dashboard.
    """
    
    missing_info: List[str] = Field(
        default_factory=list,
        description="Liste des questions CRITIQUES que l'infirmier doit poser immédiatement (ex: 'Depuis quand ?', 'Antécédents ?')."
    )
    
    protocol_alert: Optional[str] = Field(
        None, 
        description="Alerte basée sur les protocoles médicaux (ex: 'Suspicion SCA -> ECG Immediat'). Null si R.A.S."
    )
    
    data: ExtractedPatient = Field(
        ..., 
        description="L'extraction structurée stricte des données du patient."
    )