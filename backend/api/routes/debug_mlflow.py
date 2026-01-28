"""
Routes de debug pour MLflow.
"""

import os
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/mlflow-status")
async def check_mlflow_status():
    """Vérifie le statut de la connexion MLflow."""

    result = {
        "env_tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "NOT SET"),
        "mlflow_available": False,
        "tracking_uri_configured": None,
        "can_connect": False,
        "experiment_exists": False,
        "error": None,
    }

    try:
        import mlflow
        result["mlflow_available"] = True

        from api.ml.mlflow_config import MLflowConfig

        # Configuration
        result["config"] = {
            "TRACKING_URI": MLflowConfig.TRACKING_URI,
            "EXPERIMENT_NAME": MLflowConfig.EXPERIMENT_NAME,
            "MODEL_NAME": MLflowConfig.MODEL_NAME,
        }

        # Tenter la connexion
        mlflow.set_tracking_uri(MLflowConfig.TRACKING_URI)
        result["tracking_uri_configured"] = mlflow.get_tracking_uri()

        # Tester la connexion en listant les expériences
        from mlflow.tracking import MlflowClient
        client = MlflowClient()

        experiments = client.search_experiments()
        result["can_connect"] = True
        result["experiments"] = [exp.name for exp in experiments]

        # Vérifier notre expérience
        exp = client.get_experiment_by_name(MLflowConfig.EXPERIMENT_NAME)
        if exp:
            result["experiment_exists"] = True
            result["experiment_id"] = exp.experiment_id

        # Lister les modèles enregistrés
        try:
            registered_models = client.search_registered_models()
            result["registered_models"] = [m.name for m in registered_models]
        except Exception as e:
            result["registered_models_error"] = str(e)

        # Test: créer un run simple
        result["test_run"] = "skipped"

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Erreur MLflow debug: {e}", exc_info=True)

    return result


@router.post("/test-register-model")
async def test_register_model():
    """Test l'enregistrement d'un modèle via MlflowClient (compatible toutes versions)."""

    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        from api.ml.mlflow_config import MLflowConfig

        mlflow.set_tracking_uri(MLflowConfig.TRACKING_URI)
        mlflow.set_experiment(MLflowConfig.EXPERIMENT_NAME)

        client = MlflowClient()
        model_name = "test-model-debug"

        # Créer un run de test
        with mlflow.start_run(run_name="test-register") as run:
            # Log un paramètre simple
            mlflow.log_param("test_param", "value")
            mlflow.log_metric("test_metric", 0.95)

            run_id = run.info.run_id

            # Créer un modèle sklearn simple pour tester
            from sklearn.linear_model import LogisticRegression
            import numpy as np

            X = np.array([[1, 2], [3, 4], [5, 6]])
            y = np.array([0, 1, 0])
            model = LogisticRegression().fit(X, y)

            # Logger le modèle
            mlflow.sklearn.log_model(model, "test_model")

            # Enregistrer via MlflowClient (plus compatible)
            model_uri = f"runs:/{run_id}/test_model"

            # Créer le modèle enregistré s'il n'existe pas
            try:
                client.create_registered_model(model_name)
            except Exception:
                pass  # Existe déjà

            # Créer la version
            model_version = client.create_model_version(
                name=model_name,
                source=model_uri,
                run_id=run_id,
            )

            return {
                "status": "success",
                "run_id": run_id,
                "registered_model": model_name,
                "version": model_version.version,
            }

    except Exception as e:
        logger.error(f"Test register error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
