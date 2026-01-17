"""
Configuration de la base de données SQLite pour le feedback
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from src.api.core.config import settings

# Créer le dossier data s'il n'existe pas
os.makedirs("data", exist_ok=True)

# Engine SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Pour SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TriagePrediction(Base):
    """Table des prédictions de triage"""
    __tablename__ = "triage_predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Patient info
    patient_age = Column(Integer)
    patient_sexe = Column(String(1))
    motif_consultation = Column(Text)

    # Constantes vitales
    frequence_cardiaque = Column(Integer)
    frequence_respiratoire = Column(Integer)
    saturation_oxygene = Column(Float)
    pression_systolique = Column(Integer)
    pression_diastolique = Column(Integer)
    temperature = Column(Float)
    echelle_douleur = Column(Integer)

    # Prédiction
    predicted_level = Column(String(20))  # ROUGE, JAUNE, VERT, GRIS
    french_triage_level = Column(String(10))  # Tri 1, 2, 3A, 3B, 4, 5
    confidence_score = Column(Float)
    ml_score = Column(Float)
    rag_context = Column(Text, nullable=True)

    # Validation infirmière (feedback)
    validated = Column(Boolean, default=False)
    validated_at = Column(DateTime, nullable=True)
    validated_level = Column(String(20), nullable=True)  # Niveau corrigé par l'infirmière
    validator_notes = Column(Text, nullable=True)

    # Métadonnées
    model_version = Column(String(50))
    processing_time_ms = Column(Float)


class ModelRegistry(Base):
    """Table des modèles enregistrés"""
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    model_name = Column(String(100))
    version = Column(String(50))
    mlflow_run_id = Column(String(100), nullable=True)

    # Métriques
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)

    # Statut
    is_active = Column(Boolean, default=False)
    training_samples = Column(Integer, nullable=True)
    training_config = Column(JSON, nullable=True)

    # Fichiers
    model_path = Column(String(255))
    preprocessor_path = Column(String(255), nullable=True)


def init_db():
    """Initialise la base de données"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency pour obtenir une session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
