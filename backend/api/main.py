import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import triage, conversation, feedback, mlflow_routes, debug_mlflow, simulation, history, benchmark

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RedFlag API",
    description="API de Triage Medical Intelligent avec MLflow - Hugging Face Spaces",
    version="2.1.0"
)

# CORS pour permettre les appels depuis le Frontend Space
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(triage.router, prefix="/triage", tags=["Triage"])
app.include_router(conversation.router, prefix="/conversation", tags=["Conversation"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(mlflow_routes.router, tags=["MLflow"])
app.include_router(debug_mlflow.router, tags=["Debug"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
app.include_router(history.router, tags=["History"])
app.include_router(benchmark.router, prefix="/benchmark", tags=["Benchmark"])

@app.get("/")
def read_root():
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "non configure")
    return {
        "status": "online",
        "message": "Backend RedFlag-AI operationnel",
        "platform": "Hugging Face Spaces",
        "mlflow_uri": mlflow_uri
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
