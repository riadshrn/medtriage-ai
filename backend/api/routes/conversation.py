from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from typing import List, Optional
import pandas as pd
import io
import time
import uuid

# Schemas
from api.schemas.conversation import ConversationUploadResponse, DialogueMessage
from api.schemas.monitoring import SimulationResult, LLMMetrics
from api.schemas.triage import PatientInput

# Services
from api.services.triage_service import get_triage_service
from api.services.extraction_service import PatientExtractor
from api.services.agent_service import get_agent_service

router = APIRouter()

# Chemin vers les conversations (dans le conteneur: /app/data/raw/conversations)
CONVERSATIONS_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "conversations"

# Mapping des fichiers vers leurs descriptions
CONVERSATION_DESCRIPTIONS = {
    "conv1.txt": {"name": "Douleur Thoracique (SCA)", "niveau": "Tri 1-2", "icon": "heart"},
    "conv2.txt": {"name": "Douleur Abdominale (Appendicite)", "niveau": "Tri 3B", "icon": "stethoscope"},
    "conv3.txt": {"name": "Traumatisme Cheville", "niveau": "Tri 3B", "icon": "foot"},
    "conv4.txt": {"name": "Infection ORL (Rhinopharyngite)", "niveau": "Tri 5", "icon": "virus"},
    "conv5.txt": {"name": "Suspicion AVC", "niveau": "Tri 2", "icon": "brain"},
    "conv6.txt": {"name": "Douleur Pelvienne (Risque GEU)", "niveau": "Tri 3A", "icon": "warning"},
    "conv7.txt": {"name": "Confusion / Sepsis", "niveau": "Tri 2", "icon": "thermometer"},
    "conv8.txt": {"name": "Lombalgie Post-Traumatique", "niveau": "Tri 3B", "icon": "back"},
    "conv9.txt": {"name": "Bronchiolite Nourrisson", "niveau": "Tri 3A", "icon": "baby"},
}


@router.get("/list")
async def list_conversations():
    """Liste les conversations disponibles."""
    conversations = []

    if CONVERSATIONS_PATH.exists():
        for file in CONVERSATIONS_PATH.glob("*.txt"):
            if file.name == "sommaire.txt":
                continue

            desc = CONVERSATION_DESCRIPTIONS.get(file.name, {
                "name": file.stem.replace("_", " ").title(),
                "niveau": "Non classé",
                "icon": "file"
            })

            conversations.append({
                "filename": file.name,
                **desc
            })

    return sorted(conversations, key=lambda x: x["filename"])


@router.get("/load/{filename}", response_model=ConversationUploadResponse)
async def load_conversation(filename: str):
    """Charge une conversation depuis le dossier de données."""
    filepath = CONVERSATIONS_PATH / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Conversation '{filename}' non trouvée")

    if not filepath.suffix == ".txt":
        raise HTTPException(status_code=400, detail="Seuls les fichiers .txt sont supportés")

    try:
        df = pd.read_csv(filepath, header=0, engine='python')

        messages = []
        for index, row in df.iterrows():
            if len(row) > 0 and pd.notna(row.iloc[0]):
                txt = str(row.iloc[0]).strip().strip('"').strip("'")
                if txt:
                    messages.append(DialogueMessage(role="infirmier", content=txt))

            if len(row) > 1 and pd.notna(row.iloc[1]):
                txt = str(row.iloc[1]).strip().strip('"').strip("'")
                if txt:
                    messages.append(DialogueMessage(role="patient", content=txt))

        return ConversationUploadResponse(
            filename=filename,
            messages=messages,
            total_messages=len(messages)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement: {str(e)}")


@router.post("/upload", response_model=ConversationUploadResponse)
async def upload_conversation(file: UploadFile = File(...)):
    if not (file.filename.endswith('.csv') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Format supporté : .csv ou .txt")

    try:
        content = await file.read()
        try:
            df = pd.read_csv(io.BytesIO(content), header=0, engine='python')
        except Exception:
            df = pd.read_csv(io.BytesIO(content), header=0, sep=None, engine='python')

        messages = []
        for index, row in df.iterrows():
            if len(row) > 0 and pd.notna(row.iloc[0]):
                txt = str(row.iloc[0]).strip().strip('"').strip("'")
                if txt: messages.append(DialogueMessage(role="infirmier", content=txt))
            
            if len(row) > 1 and pd.notna(row.iloc[1]):
                txt = str(row.iloc[1]).strip().strip('"').strip("'")
                if txt: messages.append(DialogueMessage(role="patient", content=txt))

        return ConversationUploadResponse(
            filename=file.filename,
            messages=messages,
            total_messages=len(messages)
        )
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/process", response_model=SimulationResult)
async def process_conversation(data: ConversationUploadResponse):
    """
    Pipeline : Conversation -> LLM Extraction (avec Metrics) -> Triage
    """
    # 1. Reconstitution du dialogue
    full_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in data.messages])
    
    # 2. APPEL LLM (Extraction + Metrics)
    extractor = PatientExtractor()
    
    # --- CORRECTION ICI : ON RECUPERE LES DEUX OBJETS ---
    extracted_data, metrics = extractor.extract_from_conversation(full_text)
    # ----------------------------------------------------
    
    # 3. CONVERSION & TRIAGE
    # Maintenant extracted_data est bien l'objet Pydantic, donc .to_triage_input fonctionne
    triage_input = extractor.to_triage_input(extracted_data)
    
    triage_service = get_triage_service()
    triage_result = triage_service.predict(triage_input)
    
    # 4. RÉPONSE
    return SimulationResult(
        conversation_id=str(uuid.uuid4()),
        extracted_patient=extracted_data,
        triage_result=triage_result,
        metrics=metrics # On renvoie les métriques calculées par EcoLogits
    )

@router.post("/agent-audit")
async def audit_conversation(data: ConversationUploadResponse):
    """
    Analyse la conversation via l'Agent PydanticAI pour voir ses décisions.
    """
    full_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in data.messages])
    
    agent_service = get_agent_service()
    # On appelle la nouvelle méthode qui renvoie le raisonnement
    result = await agent_service.analyze_with_reasoning(full_text)
    
    return result