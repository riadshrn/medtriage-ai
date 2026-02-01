from pydantic import BaseModel, field_validator # <-- Import field_validator
from typing import List, Optional
from api.schemas.validators import validate_safe_input # <-- Import ton validateur

class DialogueMessage(BaseModel):
    role: str       
    content: str
    timestamp: Optional[str] = None

    # AJOUT DU GARDE-FOU
    @field_validator('content')
    @classmethod
    def check_safety(cls, v: str) -> str:
        return validate_safe_input(v)

class ConversationUploadResponse(BaseModel):
    filename: str
    messages: List[DialogueMessage]
    total_messages: int