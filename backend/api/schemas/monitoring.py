from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from api.schemas.triage import TriageResponse
from api.schemas.extraction import ExtractedPatient

class LLMMetrics(BaseModel):
    """Métriques inspirées de rag_augmented.py et schema.py du cours"""
    timestamp: datetime = Field(default_factory=datetime.now)
    provider: str
    model_name: str
    
    # Consommation Tokens
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Performance
    latency_ms: float
    
    # FinOps (Coûts)
    cost_usd: float = Field(..., description="Coût estimé en $")
    
    # GreenOps (EcoLogits)
    gwp_kgco2: Optional[float] = Field(None, description="Impact Carbone (kgCO2eq)")
    energy_kwh: Optional[float] = Field(None, description="Consommation énergétique (kWh)")

class SimulationResult(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    conversation_id: str
    extracted_patient: ExtractedPatient 
    triage_result: TriageResponse
    metrics: LLMMetrics