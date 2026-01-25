from pydantic import BaseModel
from typing import List, Optional

class DialogueMessage(BaseModel):
    role: str       # "infirmier" ou "patient"
    content: str
    timestamp: Optional[str] = None

class ConversationUploadResponse(BaseModel):
    filename: str
    messages: List[DialogueMessage]
    total_messages: int