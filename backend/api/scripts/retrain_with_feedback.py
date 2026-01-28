#!/usr/bin/env python
"""
Script de reentrainement du modele avec feedback.

Ce script:
1. Charge les donnees d'entrainement originales
2. Recupere les feedbacks des infirmieres
3. Combine les deux datasets
4. Entraine un nouveau modele
5. L'enregistre dans MLflow

Usage:
    python src/api/scripts/retrain_with_feedback.py [options]

Options:
    --data PATH         Chemin vers les donnees originales (default: data/raw/patients_synthetic.csv)
    --min-feedback N    Nombre minimum de feedbacks requis (default: 50)
    --no-feedback       Entrainer sans les feedbacks
    --output PATH       Dossier de sortie pour le modele (default: models/trained)
    --run-name NAME     Nom du run MLflow
    --tune              Activer le hyperparameter tuning
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from api.ml.trainer import ModelTrainer
from api.ml.feedback_handler import get_feedback_handler
from api.ml.mlflow_config import MLflowConfig, MLFLOW_AVAILABLE

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Reentrainement du modele avec feedback des infirmieres"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/raw/patients_synthetic.csv",
        help="Chemin vers les donnees originales"
    )
    parser.add_argument(
        "--min-feedback",
        type=int,
        default=50,
        help="Nombre minimum de feedbacks requis"
    )
    parser.add_argument(
        "--no-feedback",
        action="store_true",
        help="Entrainer sans les feedbacks"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/trained",
        help="Dossier de sortie"
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Nom du run MLflow"
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Activer le hyperparameter tuning"
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Nombre d'arbres XGBoost"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Profondeur maximale"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.1,
        help="Taux d'apprentissage"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("REENTRAINEMENT DU MODELE AVEC FEEDBACK")
    logger.info("=" * 60)

    # Verifier que les donnees existent
    if not Path(args.data).exists():
        logger.error(f"Fichier de donnees non trouve: {args.data}")
        sys.exit(1)

    # Initialiser le trainer
    trainer = ModelTrainer()

    # Charger les donnees originales
    logger.info(f"Chargement des donnees: {args.data}")
    original_df = trainer.preprocessor.load_data(args.data)
    logger.info(f"Donnees originales: {len(original_df)} echantillons")

    # Recuperer les feedbacks si demande
    feedback_df = pd.DataFrame()
    if not args.no_feedback:
        handler = get_feedback_handler()
        feedback_df = handler.get_feedback_for_retraining(
            min_samples=args.min_feedback
        )

        if feedback_df.empty:
            logger.warning(
                f"Pas assez de feedbacks ({handler.get_feedback_count()} < {args.min_feedback}). "
                f"Entrainement avec les donnees originales uniquement."
            )
        else:
            logger.info(f"Feedbacks recuperes: {len(feedback_df)} corrections")

    # Combiner les datasets
    if not feedback_df.empty:
        combined_df = pd.concat([original_df, feedback_df], ignore_index=True)
        logger.info(f"Dataset combine: {len(combined_df)} echantillons")
    else:
        combined_df = original_df

    # Sauvegarder le dataset combine
    combined_path = Path("data/processed/combined_training.csv")
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(combined_path, index=False)
    logger.info(f"Dataset sauvegarde: {combined_path}")

    # Generer le nom du run
    run_name = args.run_name or f"retrain-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    tags = {
        "trigger": "script",
        "feedback_samples": str(len(feedback_df)),
        "original_samples": str(len(original_df)),
    }

    # Entrainement
    if args.tune:
        logger.info("Mode: Hyperparameter tuning")
        classifier = trainer.train_with_tuning(
            csv_path=str(combined_path),
            run_name=run_name,
        )
    else:
        logger.info("Mode: Entrainement standard")
        classifier = trainer.train_from_csv(
            csv_path=str(combined_path),
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            run_name=run_name,
            tags=tags,
            register_model=True,
        )

    # Sauvegarder le modele localement
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "triage_model.json"
    preprocessor_path = output_dir / "preprocessor.pkl"

    classifier.save(
        model_path=str(model_path),
        preprocessor_path=str(preprocessor_path)
    )

    logger.info(f"Modele sauvegarde: {model_path}")
    logger.info(f"Preprocesseur sauvegarde: {preprocessor_path}")

    # Afficher le resume
    logger.info("=" * 60)
    logger.info("RESUME")
    logger.info("=" * 60)
    logger.info(f"Donnees originales: {len(original_df)}")
    logger.info(f"Feedbacks utilises: {len(feedback_df)}")
    logger.info(f"Total echantillons: {len(combined_df)}")
    logger.info(f"MLflow disponible: {MLFLOW_AVAILABLE}")

    if MLFLOW_AVAILABLE:
        logger.info(f"MLflow Tracking URI: {MLflowConfig.TRACKING_URI}")
        logger.info(f"Experiment: {MLflowConfig.EXPERIMENT_NAME}")
        logger.info(f"Model Registry: {MLflowConfig.MODEL_NAME}")

    logger.info("=" * 60)
    logger.info("REENTRAINEMENT TERMINE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
