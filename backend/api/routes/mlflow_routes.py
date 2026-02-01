"""
Routes API pour consulter les modeles MLflow.

Endpoints:
- GET /models/list : Liste tous les modeles avec metriques
- GET /models/latest : Dernier modele en production
- GET /models/{version} : Details d'une version specifique
- GET /models/experiments : Liste des experiences
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.ml.mlflow_config import MLflowConfig, MLFLOW_AVAILABLE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["MLflow Models"])


# =============================================================================
# SCHEMAS DE REPONSE
# =============================================================================

class ModelMetrics(BaseModel):
    """Metriques d'un modele."""
    accuracy: Optional[float] = None
    f1_macro: Optional[float] = None
    precision_macro: Optional[float] = None
    recall_macro: Optional[float] = None
    cv_accuracy_mean: Optional[float] = None
    latency_per_sample_ms: Optional[float] = None


class ModelVersion(BaseModel):
    """Information sur une version de modele."""
    version: int
    name: str
    stage: str  # None, Staging, Production, Archived
    status: str
    run_id: str
    created_at: datetime
    metrics: Optional[ModelMetrics] = None
    tags: Optional[dict] = None
    description: Optional[str] = None


class ModelListResponse(BaseModel):
    """Liste des modeles."""
    model_name: str
    total_versions: int
    production_version: Optional[int] = None
    staging_version: Optional[int] = None
    versions: List[ModelVersion]


class ExperimentInfo(BaseModel):
    """Information sur une experience."""
    name: str
    experiment_id: str
    lifecycle_stage: str
    total_runs: int = 0


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/list", response_model=ModelListResponse)
async def list_all_models():
    """
    Liste tous les modeles enregistres avec leurs metriques.

    Retourne toutes les versions du modele avec:
    - Date de creation
    - Stage (Production/Staging/Archived)
    - Metriques d'entrainement
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MLflow non disponible. Installez mlflow avec: pip install mlflow"
        )

    if not MLflowConfig.setup():
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de se connecter a MLflow: {MLflowConfig.TRACKING_URI}"
        )

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()

        # Recuperer toutes les versions du modele
        try:
            versions = client.search_model_versions(f"name='{MLflowConfig.MODEL_NAME}'")
        except Exception:
            # Modele pas encore enregistre
            return ModelListResponse(
                model_name=MLflowConfig.MODEL_NAME,
                total_versions=0,
                versions=[]
            )

        # Construire la liste des versions avec metriques
        model_versions = []
        production_version = None
        staging_version = None

        for mv in sorted(versions, key=lambda x: int(x.version), reverse=True):
            # Recuperer les metriques du run associe
            metrics = None
            tags = None

            if mv.run_id:
                try:
                    run = client.get_run(mv.run_id)
                    metrics = ModelMetrics(
                        accuracy=run.data.metrics.get("accuracy"),
                        f1_macro=run.data.metrics.get("f1_macro"),
                        precision_macro=run.data.metrics.get("precision_macro"),
                        recall_macro=run.data.metrics.get("recall_macro"),
                        cv_accuracy_mean=run.data.metrics.get("cv_accuracy_mean"),
                        latency_per_sample_ms=run.data.metrics.get("latency_per_sample_ms"),
                    )
                    tags = run.data.tags
                except Exception as e:
                    logger.warning(f"Impossible de recuperer le run {mv.run_id}: {e}")

            # Tracker les versions production/staging
            if mv.current_stage == "Production":
                production_version = int(mv.version)
            elif mv.current_stage == "Staging":
                staging_version = int(mv.version)

            model_versions.append(ModelVersion(
                version=int(mv.version),
                name=mv.name,
                stage=mv.current_stage or "None",
                status=mv.status,
                run_id=mv.run_id or "",
                created_at=datetime.fromtimestamp(mv.creation_timestamp / 1000),
                metrics=metrics,
                tags=tags,
                description=mv.description,
            ))

        return ModelListResponse(
            model_name=MLflowConfig.MODEL_NAME,
            total_versions=len(model_versions),
            production_version=production_version,
            staging_version=staging_version,
            versions=model_versions,
        )

    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des modeles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_model():
    """
    Retourne les informations du dernier modele en production.
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLflow non disponible")

    MLflowConfig.setup()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()

        from mlflow.exceptions import RestException

        try:
            # Utiliser search_model_versions au lieu de get_latest_versions (déprécié depuis MLflow 2.9)
            all_versions = client.search_model_versions(f"name='{MLflowConfig.MODEL_NAME}'")
        except RestException as e:
            # Le modèle n'existe pas encore dans le registry
            if "RESOURCE_DOES_NOT_EXIST" in str(e):
                return {
                    "message": "Modele non encore enregistre dans MLflow Model Registry",
                    "model_name": MLflowConfig.MODEL_NAME
                }
            raise

        if not all_versions:
            return {"message": "Aucun modele enregistre", "model_name": MLflowConfig.MODEL_NAME}

        # Chercher d'abord une version en Production
        prod_versions = [v for v in all_versions if v.current_stage == "Production"]
        if prod_versions:
            latest = max(prod_versions, key=lambda x: int(x.version))
        else:
            # Sinon prendre la dernière version
            latest = max(all_versions, key=lambda x: int(x.version))

        # Recuperer les metriques
        metrics = {}
        if latest.run_id:
            run = client.get_run(latest.run_id)
            metrics = run.data.metrics

        return {
            "model_name": latest.name,
            "version": int(latest.version),
            "stage": latest.current_stage or "None",
            "status": latest.status,
            "run_id": latest.run_id,
            "created_at": datetime.fromtimestamp(latest.creation_timestamp / 1000).isoformat(),
            "metrics": metrics,
            "model_uri": f"models:/{MLflowConfig.MODEL_NAME}/{latest.version}",
        }

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{version}")
async def get_model_version(version: int):
    """
    Retourne les details d'une version specifique du modele.
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLflow non disponible")

    MLflowConfig.setup()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()
        mv = client.get_model_version(MLflowConfig.MODEL_NAME, str(version))

        # Recuperer les metriques et params du run
        metrics = {}
        params = {}
        tags = {}

        if mv.run_id:
            run = client.get_run(mv.run_id)
            metrics = run.data.metrics
            params = run.data.params
            tags = run.data.tags

        return {
            "model_name": mv.name,
            "version": int(mv.version),
            "stage": mv.current_stage or "None",
            "status": mv.status,
            "run_id": mv.run_id,
            "created_at": datetime.fromtimestamp(mv.creation_timestamp / 1000).isoformat(),
            "description": mv.description,
            "metrics": metrics,
            "params": params,
            "tags": tags,
            "model_uri": f"models:/{MLflowConfig.MODEL_NAME}/{version}",
        }

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments", response_model=List[ExperimentInfo])
async def list_experiments():
    """
    Liste toutes les experiences MLflow.
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLflow non disponible")

    MLflowConfig.setup()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()
        experiments = client.search_experiments()

        result = []
        for exp in experiments:
            # Compter les runs
            runs = client.search_runs(experiment_ids=[exp.experiment_id], max_results=1)

            result.append(ExperimentInfo(
                name=exp.name,
                experiment_id=exp.experiment_id,
                lifecycle_stage=exp.lifecycle_stage,
                total_runs=len(runs),  # Approximatif
            ))

        return result

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
async def list_runs(
    experiment_name: Optional[str] = Query(None, description="Nom de l'experience"),
    limit: int = Query(20, description="Nombre max de runs"),
    order_by: str = Query("start_time DESC", description="Ordre de tri")
):
    """
    Liste les runs d'entrainement avec leurs metriques.
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLflow non disponible")

    MLflowConfig.setup()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()

        # Determiner l'experience
        exp_name = experiment_name or MLflowConfig.EXPERIMENT_NAME
        experiment = client.get_experiment_by_name(exp_name)

        if not experiment:
            return {"message": f"Experience '{exp_name}' non trouvee", "runs": []}

        # Recuperer les runs
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            max_results=limit,
            order_by=[order_by],
        )

        result = []
        for run in runs:
            result.append({
                "run_id": run.info.run_id,
                "run_name": run.info.run_name,
                "status": run.info.status,
                "start_time": datetime.fromtimestamp(run.info.start_time / 1000).isoformat(),
                "end_time": datetime.fromtimestamp(run.info.end_time / 1000).isoformat() if run.info.end_time else None,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": {k: v for k, v in run.data.tags.items() if not k.startswith("mlflow.")},
            })

        return {
            "experiment_name": exp_name,
            "total_runs": len(result),
            "runs": result,
        }

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote/{version}")
async def promote_model(version: int, stage: str = Query("Production", regex="^(Staging|Production)$")):
    """
    Promouvoit une version du modele vers Staging ou Production.
    """
    if not MLFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLflow non disponible")

    MLflowConfig.setup()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        client = MlflowClient()

        # Archiver l'ancien modele du meme stage
        current_versions = client.get_latest_versions(MLflowConfig.MODEL_NAME, stages=[stage])
        for cv in current_versions:
            if int(cv.version) != version:
                client.transition_model_version_stage(
                    MLflowConfig.MODEL_NAME,
                    cv.version,
                    "Archived"
                )
                logger.info(f"Version {cv.version} archivee")

        # Promouvoir la nouvelle version
        client.transition_model_version_stage(
            MLflowConfig.MODEL_NAME,
            str(version),
            stage
        )

        return {
            "status": "success",
            "message": f"Version {version} promue en {stage}",
            "model_name": MLflowConfig.MODEL_NAME,
            "version": version,
            "stage": stage,
        }

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))
