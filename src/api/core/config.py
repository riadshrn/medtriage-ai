"""
Configuration de l'API FastAPI
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configuration de l'application"""

    # API
    API_TITLE: str = "RedFlag-AI API"
    API_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",  # Streamlit local
        "http://localhost:3000",  # Dev frontend
        "https://*.hf.space",     # Hugging Face Spaces
        "*"                        # Permissif pour le dev
    ]

    # Base de données
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/feedback.db")

    # Modèles ML
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "models/trained/triage_model.json")
    ML_PREPROCESSOR_PATH: str = os.getenv("ML_PREPROCESSOR_PATH", "models/trained/preprocessor.pkl")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "data/vector_store/medical_kb.pkl")

    # MLflow
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///./data/mlflow.db")
    MLFLOW_EXPERIMENT_NAME: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "redflag-triage")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
