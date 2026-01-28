"""
Configuration et utilitaires MLflow pour MedTriage-AI.

Ce module gere:
- Connection au serveur MLflow
- Gestion des experiences
- Acces au Model Registry
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Tentative d'import MLflow (optionnel)
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow non installe. Fonctionnalites de tracking desactivees.")


class MLflowConfig:
    """Configuration et utilitaires pour MLflow."""

    # Configuration via variables d'environnement
    TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "medtriage-classification")
    MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "medtriage-classifier")

    # Stages du Model Registry
    STAGE_STAGING = "Staging"
    STAGE_PRODUCTION = "Production"
    STAGE_ARCHIVED = "Archived"

    _initialized = False
    _client: Optional[Any] = None

    @classmethod
    def is_available(cls) -> bool:
        """Verifie si MLflow est disponible."""
        return MLFLOW_AVAILABLE

    @classmethod
    def setup(cls) -> bool:
        """
        Initialise la connection MLflow.

        Returns:
            True si initialise avec succes, False sinon
        """
        if not MLFLOW_AVAILABLE:
            logger.warning("MLflow non disponible, tracking desactive")
            return False

        if cls._initialized:
            return True

        try:
            mlflow.set_tracking_uri(cls.TRACKING_URI)

            # Creer ou recuperer l'experience
            experiment = mlflow.get_experiment_by_name(cls.EXPERIMENT_NAME)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    cls.EXPERIMENT_NAME,
                    tags={"project": "medtriage-ai", "team": "ml"}
                )
                logger.info(f"Experience MLflow creee: {cls.EXPERIMENT_NAME} (id={experiment_id})")
            else:
                logger.info(f"Experience MLflow existante: {cls.EXPERIMENT_NAME}")

            mlflow.set_experiment(cls.EXPERIMENT_NAME)
            cls._client = MlflowClient()
            cls._initialized = True
            logger.info(f"MLflow configure: {cls.TRACKING_URI}")
            return True

        except Exception as e:
            logger.error(f"Erreur initialisation MLflow: {e}")
            return False

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """Retourne le client MLflow."""
        if not cls._initialized:
            cls.setup()
        return cls._client

    @classmethod
    def get_production_model_uri(cls) -> Optional[str]:
        """
        Retourne l'URI du modele en production.

        Returns:
            URI du modele ou None si non trouve
        """
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return None

        try:
            latest_versions = cls._client.get_latest_versions(
                cls.MODEL_NAME,
                stages=[cls.STAGE_PRODUCTION]
            )
            if latest_versions:
                version = latest_versions[0]
                uri = f"models:/{cls.MODEL_NAME}/{cls.STAGE_PRODUCTION}"
                logger.info(f"Modele production trouve: {uri} (v{version.version})")
                return uri
            return None
        except Exception as e:
            logger.warning(f"Impossible de recuperer le modele production: {e}")
            return None

    @classmethod
    def get_staging_model_uri(cls) -> Optional[str]:
        """Retourne l'URI du modele en staging."""
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return None

        try:
            latest_versions = cls._client.get_latest_versions(
                cls.MODEL_NAME,
                stages=[cls.STAGE_STAGING]
            )
            if latest_versions:
                return f"models:/{cls.MODEL_NAME}/{cls.STAGE_STAGING}"
            return None
        except Exception as e:
            logger.warning(f"Impossible de recuperer le modele staging: {e}")
            return None

    @classmethod
    def get_latest_model_version(cls) -> Optional[int]:
        """Retourne le numero de la derniere version du modele."""
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return None

        try:
            versions = cls._client.search_model_versions(f"name='{cls.MODEL_NAME}'")
            if versions:
                return max(int(v.version) for v in versions)
            return None
        except Exception as e:
            logger.warning(f"Impossible de recuperer la derniere version: {e}")
            return None

    @classmethod
    def get_model_info(cls, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations d'un modele.

        Args:
            version: Numero de version (dernier si None)

        Returns:
            Dictionnaire avec les infos du modele
        """
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return None

        try:
            if version is None:
                version = cls.get_latest_model_version()

            if version is None:
                return None

            model_version = cls._client.get_model_version(
                cls.MODEL_NAME,
                str(version)
            )

            return {
                "name": model_version.name,
                "version": model_version.version,
                "stage": model_version.current_stage,
                "status": model_version.status,
                "run_id": model_version.run_id,
                "creation_timestamp": model_version.creation_timestamp,
            }
        except Exception as e:
            logger.warning(f"Impossible de recuperer les infos du modele: {e}")
            return None

    @classmethod
    def promote_to_production(cls, version: int) -> bool:
        """
        Promouvoit une version du modele en production.

        Args:
            version: Numero de version a promouvoir

        Returns:
            True si succes, False sinon
        """
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return False

        try:
            # Archiver l'ancien modele production
            current_prod = cls._client.get_latest_versions(
                cls.MODEL_NAME,
                stages=[cls.STAGE_PRODUCTION]
            )
            for mv in current_prod:
                cls._client.transition_model_version_stage(
                    cls.MODEL_NAME,
                    mv.version,
                    cls.STAGE_ARCHIVED
                )
                logger.info(f"Modele v{mv.version} archive")

            # Promouvoir la nouvelle version
            cls._client.transition_model_version_stage(
                cls.MODEL_NAME,
                str(version),
                cls.STAGE_PRODUCTION
            )
            logger.info(f"Modele v{version} promu en production")
            return True

        except Exception as e:
            logger.error(f"Erreur promotion modele: {e}")
            return False

    @classmethod
    def list_experiments(cls) -> list:
        """Liste toutes les experiences MLflow."""
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return []

        try:
            experiments = cls._client.search_experiments()
            return [
                {
                    "name": exp.name,
                    "experiment_id": exp.experiment_id,
                    "lifecycle_stage": exp.lifecycle_stage,
                }
                for exp in experiments
            ]
        except Exception as e:
            logger.warning(f"Erreur listage experiences: {e}")
            return []

    @classmethod
    def get_run_metrics(cls, run_id: str) -> Optional[Dict[str, float]]:
        """Recupere les metriques d'un run."""
        if not MLFLOW_AVAILABLE or not cls._initialized:
            if not cls.setup():
                return None

        try:
            run = cls._client.get_run(run_id)
            return run.data.metrics
        except Exception as e:
            logger.warning(f"Erreur recuperation metriques: {e}")
            return None
