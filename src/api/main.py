import logging
from fastapi import FastAPI

from src.api.routes import triage, conversation, feedback, mlflow_routes

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="RedFlag API",
    description="API de Triage Medical Intelligent avec MLflow",
    version="2.1.0"
)

# Inclusion des routers
app.include_router(triage.router, prefix="/triage", tags=["Triage"])
app.include_router(conversation.router, prefix="/conversation", tags=["Conversation"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(mlflow_routes.router, tags=["MLflow"])

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend RedFlag-AI opérationnel"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}