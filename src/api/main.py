from fastapi import FastAPI
# 1. On importe le routeur qu'on vient de créer
from src.api.routes import triage # <--- NOUVEAU

app = FastAPI(
    title="RedFlag API",
    description="API de Triage Médical Intelligent",
    version="2.0.0"
)

# 2. On l'inclut dans l'application
# prefix="/triage" signifie que toutes les routes commenceront par /triage
app.include_router(triage.router, prefix="/triage", tags=["Triage"]) # <--- NOUVEAU

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend RedFlag-AI opérationnel"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}