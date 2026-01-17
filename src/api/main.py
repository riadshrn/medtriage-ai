"""
RedFlag-AI - FastAPI Backend
API REST pour le système de triage des urgences
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.routes import triage, models, feedback, health
from src.api.core.config import settings
from src.api.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation et cleanup de l'application"""
    # Startup
    print("=" * 60)
    print("REDFLAG-AI API - Démarrage")
    print("=" * 60)

    # Initialiser la base de données SQLite
    init_db()
    print("Base de données initialisée")

    yield

    # Shutdown
    print("REDFLAG-AI API - Arrêt")


app = FastAPI(
    title="RedFlag-AI API",
    description="""
    ## API de Triage des Urgences

    Système d'aide à la décision pour le triage des patients aux urgences,
    basé sur la grille FRENCH (FRench Emergency Nurses Classification in-Hospital).

    ### Fonctionnalités
    - **Triage automatique** : Classification des patients en 4 niveaux de gravité
    - **Validation infirmière** : Feedback loop pour améliorer le modèle
    - **Gestion des modèles** : MLflow pour le versioning et le réentraînement

    ### Niveaux de gravité
    - 🔴 **ROUGE** : Urgence vitale (Tri 1-2 FRENCH)
    - 🟡 **JAUNE** : Urgence relative (Tri 3A-3B FRENCH)
    - 🟢 **VERT** : Non urgent (Tri 4 FRENCH)
    - ⚪ **GRIS** : Ne nécessite pas les urgences (Tri 5 FRENCH)
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS pour permettre l'accès depuis Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(health.router, tags=["Health"])
app.include_router(triage.router, prefix="/api/v1", tags=["Triage"])
app.include_router(models.router, prefix="/api/v1", tags=["Models"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])


@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "name": "RedFlag-AI API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
