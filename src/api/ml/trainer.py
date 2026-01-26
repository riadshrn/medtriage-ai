"""
Entrainement du modele de classification avec support MLflow.

Ce module gere:
- Entrainement du modele XGBoost
- Validation croisee
- Hyperparameter tuning
- Tracking MLflow (metriques, parametres, artefacts)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from .classifier import TriageClassifier
from .preprocessor import TriagePreprocessor
from .mlflow_config import MLflowConfig, MLFLOW_AVAILABLE
from .feature_config import ALL_ML_FEATURES

logger = logging.getLogger(__name__)

# Import MLflow si disponible
if MLFLOW_AVAILABLE:
    import mlflow
    import mlflow.xgboost


class ModelTrainer:
    """
    Gere l'entrainement du modele de classification.

    Inclut :
    - Split train/test
    - Validation croisee
    - Hyperparameter tuning (optionnel)
    - Tracking MLflow
    """

    def __init__(self, random_state: int = 42):
        """
        Initialise le trainer.

        Args:
            random_state: Graine aleatoire
        """
        self.random_state = random_state
        self.classifier: Optional[TriageClassifier] = None
        self.preprocessor = TriagePreprocessor()
        self._mlflow_enabled = False

        # Initialiser MLflow si disponible
        if MLFLOW_AVAILABLE:
            self._mlflow_enabled = MLflowConfig.setup()

    def train_from_csv(
        self,
        csv_path: str,
        test_size: float = 0.2,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        cv_folds: int = 5,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        register_model: bool = True,
    ) -> TriageClassifier:
        """
        Entraine le modele depuis un fichier CSV.

        Args:
            csv_path: Chemin vers le CSV de donnees
            test_size: Proportion du test set
            n_estimators: Nombre d'arbres XGBoost
            max_depth: Profondeur maximale des arbres
            learning_rate: Taux d'apprentissage
            cv_folds: Nombre de folds pour la validation croisee
            run_name: Nom du run MLflow (optionnel)
            tags: Tags MLflow (optionnel)
            register_model: Si True, enregistre le modele dans le registry

        Returns:
            TriageClassifier: Modele entraine
        """
        logger.info("=" * 60)
        logger.info("ENTRAINEMENT DU MODELE DE CLASSIFICATION")
        logger.info("=" * 60)

        # Generer un nom de run par defaut
        if run_name is None:
            run_name = f"training-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Context manager MLflow (ou no-op si non disponible)
        mlflow_context = self._get_mlflow_context(run_name)

        with mlflow_context:
            # Logger les parametres
            self._log_params({
                "csv_path": csv_path,
                "test_size": test_size,
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "learning_rate": learning_rate,
                "cv_folds": cv_folds,
                "random_state": self.random_state,
            })

            # Logger les tags
            if tags:
                self._log_tags(tags)

            # Chargement des donnees
            df = self.preprocessor.load_data(csv_path)
            self._log_params({"n_samples": len(df)})

            # Preparation train/test
            X_train, X_test, y_train, y_test = self.preprocessor.prepare_train_test(
                df, test_size=test_size, random_state=self.random_state
            )

            # Logger la config des features
            self._log_artifact_dict(
                {"features": self.preprocessor.get_feature_names()},
                "feature_config.json"
            )

            # Creation du classificateur
            self.classifier = TriageClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=self.random_state,
            )

            # Copie du preprocesseur fitte
            self.classifier.preprocessor = self.preprocessor

            # Validation croisee sur le train set
            cv_mean, cv_std = 0.0, 0.0
            if cv_folds > 1:
                logger.info(f"Validation croisee ({cv_folds} folds)...")
                cv_scores = cross_val_score(
                    self.classifier.model,
                    X_train,
                    y_train,
                    cv=cv_folds,
                    scoring="accuracy",
                )
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
                logger.info(f"Accuracy CV : {cv_mean:.4f} (+/- {cv_std:.4f})")

                self._log_metrics({
                    "cv_accuracy_mean": cv_mean,
                    "cv_accuracy_std": cv_std,
                })

            # Entrainement sur tout le train set
            logger.info("Entrainement sur le train set...")
            self.classifier.train(X_train, y_train)

            # Evaluation sur le test set
            logger.info("Evaluation sur le test set...")
            y_pred, y_proba, latency = self.classifier.predict(X_test)

            # Calcul des metriques
            metrics = self._compute_metrics(y_test, y_pred, latency, len(X_test))
            self._log_metrics(metrics)

            logger.info(f"Accuracy test : {metrics['accuracy']:.4f}")
            logger.info(f"F1 macro : {metrics['f1_macro']:.4f}")
            logger.info(f"Latence moyenne : {metrics['latency_per_sample_ms']:.2f}ms par patient")

            # Logger la matrice de confusion
            self._log_confusion_matrix(y_test, y_pred)

            # Importance des features
            logger.info("Importance des features :")
            feature_importance = self.classifier.get_feature_importance()
            sorted_features = sorted(
                feature_importance.items(), key=lambda x: x[1], reverse=True
            )
            for feature, importance in sorted_features[:10]:
                logger.info(f"  {feature:25} : {importance:.4f}")

            # Logger le modele
            if self._mlflow_enabled and register_model:
                self._log_model(X_test, register=True)

            logger.info("=" * 60)
            logger.info("ENTRAINEMENT TERMINE")
            logger.info("=" * 60)

            return self.classifier

    def train_with_tuning(
        self,
        csv_path: str,
        test_size: float = 0.2,
        cv_folds: int = 3,
        run_name: Optional[str] = None,
    ) -> TriageClassifier:
        """
        Entraine le modele avec recherche d'hyperparametres.

        Args:
            csv_path: Chemin vers le CSV de donnees
            test_size: Proportion du test set
            cv_folds: Nombre de folds pour la recherche
            run_name: Nom du run MLflow

        Returns:
            TriageClassifier: Modele entraine avec les meilleurs hyperparametres
        """
        from sklearn.model_selection import RandomizedSearchCV

        if run_name is None:
            run_name = f"tuning-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info("=" * 60)
        logger.info("ENTRAINEMENT AVEC HYPERPARAMETER TUNING")
        logger.info("=" * 60)

        mlflow_context = self._get_mlflow_context(run_name)

        with mlflow_context:
            # Chargement des donnees
            df = self.preprocessor.load_data(csv_path)
            X_train, X_test, y_train, y_test = self.preprocessor.prepare_train_test(
                df, test_size=test_size, random_state=self.random_state
            )

            # Espace de recherche
            param_distributions = {
                "n_estimators": [50, 100, 200],
                "max_depth": [3, 6, 9],
                "learning_rate": [0.01, 0.1, 0.3],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
            }

            self._log_params({
                "tuning_method": "RandomizedSearchCV",
                "n_iter": 20,
                "cv_folds": cv_folds,
            })
            self._log_tags({"type": "hyperparameter_tuning"})

            # Modele de base
            base_model = TriageClassifier(random_state=self.random_state).model

            # Recherche aleatoire
            logger.info("Recherche d'hyperparametres...")
            random_search = RandomizedSearchCV(
                base_model,
                param_distributions,
                n_iter=20,
                cv=cv_folds,
                scoring="accuracy",
                random_state=self.random_state,
                n_jobs=-1,
                verbose=1,
            )

            random_search.fit(X_train, y_train)

            logger.info(f"Meilleurs parametres : {random_search.best_params_}")
            logger.info(f"Meilleur score CV : {random_search.best_score_:.4f}")

            # Logger les meilleurs parametres
            self._log_params({"best_" + k: v for k, v in random_search.best_params_.items()})
            self._log_metrics({"best_cv_score": random_search.best_score_})

            # Creation du classificateur avec les meilleurs parametres
            self.classifier = TriageClassifier(**random_search.best_params_)
            self.classifier.preprocessor = self.preprocessor
            self.classifier.model = random_search.best_estimator_
            self.classifier.is_trained = True

            # Evaluation sur le test set
            logger.info("Evaluation sur le test set...")
            y_pred, y_proba, latency = self.classifier.predict(X_test)

            metrics = self._compute_metrics(y_test, y_pred, latency, len(X_test))
            self._log_metrics(metrics)

            logger.info(f"Accuracy test : {metrics['accuracy']:.4f}")

            # Logger le modele
            if self._mlflow_enabled:
                self._log_model(X_test, register=True)

            logger.info("=" * 60)
            logger.info("ENTRAINEMENT TERMINE")
            logger.info("=" * 60)

            return self.classifier

    def _compute_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        latency: float,
        n_samples: int,
    ) -> Dict[str, float]:
        """Calcule les metriques d'evaluation."""
        return {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
            "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
            "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
            "precision_weighted": precision_score(y_true, y_pred, average="weighted", zero_division=0),
            "recall_weighted": recall_score(y_true, y_pred, average="weighted", zero_division=0),
            "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
            "latency_total_s": latency,
            "latency_per_sample_ms": (latency / n_samples) * 1000,
        }

    def _get_mlflow_context(self, run_name: str):
        """Retourne le context manager MLflow ou un no-op."""
        if self._mlflow_enabled:
            return mlflow.start_run(run_name=run_name)
        else:
            from contextlib import nullcontext
            return nullcontext()

    def _log_params(self, params: Dict[str, Any]):
        """Log des parametres vers MLflow."""
        if self._mlflow_enabled:
            mlflow.log_params(params)

    def _log_metrics(self, metrics: Dict[str, float]):
        """Log des metriques vers MLflow."""
        if self._mlflow_enabled:
            mlflow.log_metrics(metrics)

    def _log_tags(self, tags: Dict[str, str]):
        """Log des tags vers MLflow."""
        if self._mlflow_enabled:
            mlflow.set_tags(tags)

    def _log_artifact_dict(self, data: dict, filename: str):
        """Log un dictionnaire comme artefact JSON."""
        if self._mlflow_enabled:
            import json
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f, indent=2)
                f.flush()
                mlflow.log_artifact(f.name, artifact_path="config")

    def _log_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Log la matrice de confusion comme image."""
        if not self._mlflow_enabled:
            return

        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend non-interactif
            import matplotlib.pyplot as plt
            from sklearn.metrics import ConfusionMatrixDisplay

            fig, ax = plt.subplots(figsize=(8, 6))
            class_names = self.preprocessor.get_class_names()

            ConfusionMatrixDisplay.from_predictions(
                y_true, y_pred,
                display_labels=class_names,
                ax=ax,
                cmap='Blues'
            )
            plt.title("Matrice de Confusion")
            plt.tight_layout()

            mlflow.log_figure(fig, "confusion_matrix.png")
            plt.close()

        except Exception as e:
            logger.warning(f"Impossible de logger la matrice de confusion: {e}")

    def _log_model(self, X_sample: np.ndarray, register: bool = True):
        """Log le modele vers MLflow."""
        if not self._mlflow_enabled or self.classifier is None:
            return

        try:
            # Inferer la signature
            from mlflow.models.signature import infer_signature
            y_pred, _, _ = self.classifier.predict(X_sample[:5])
            signature = infer_signature(X_sample[:5], y_pred)

            # Logger le modele XGBoost
            model_info = mlflow.xgboost.log_model(
                #self.classifier.model,
                self.classifier.model.get_booster(),
                artifact_path="model",
                signature=signature,
                input_example=X_sample[:2],
                registered_model_name=MLflowConfig.MODEL_NAME if register else None,
            )

            logger.info(f"Modele logue: {model_info.model_uri}")

            # Logger le preprocesseur comme artefact
            import tempfile
            import pickle
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                pickle.dump(self.preprocessor, f)
                f.flush()
                mlflow.log_artifact(f.name, artifact_path="preprocessor")

        except Exception as e:
            logger.error(f"Erreur lors du logging du modele: {e}")
