from fastapi import FastAPI

from src.api.routes import conversation, simulation, triage

app = FastAPI(
    title="RedFlag API",
    description="API de Triage Médical Intelligent",
    version="2.0.0"
)

app.include_router(triage.router, prefix="/triage", tags=["Triage"])
app.include_router(conversation.router, prefix="/conversation", tags=["Conversation"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend RedFlag-AI opérationnel"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}