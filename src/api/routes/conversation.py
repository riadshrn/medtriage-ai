from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import time
import uuid

# Schemas
from src.api.schemas.conversation import ConversationUploadResponse, DialogueMessage
from src.api.schemas.monitoring import SimulationResult, LLMMetrics
from src.api.schemas.triage import PatientInput

# Services
from src.api.services.triage_service import get_triage_service
from src.api.services.extraction_service import PatientExtractor

router = APIRouter()

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