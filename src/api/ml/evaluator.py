"""
Évaluation des performances du modèle de classification.
"""

import numpy as np
from typing import Dict
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from .classifier import TriageClassifier


class ModelEvaluator:
    """
    Évalue les performances d'un modèle de classification.

    Métriques :
    - Accuracy, Precision, Recall, F1-score
    - Matrice de confusion
    - Rapport de classification détaillé
    """

    @staticmethod
    def evaluate(
        classifier: TriageClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Dict:
        """
        Évalue le modèle sur un test set.

        Args:
            classifier: Modèle à évaluer
            X_test: Features de test
            y_test: Labels de test

        Returns:
            Dict: Dictionnaire des métriques
        """
        # Prédictions
        y_pred, y_proba, latency = classifier.predict(X_test)

        # Métriques globales
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision_macro": precision_score(y_test, y_pred, average="macro"),
            "recall_macro": recall_score(y_test, y_pred, average="macro"),
            "f1_macro": f1_score(y_test, y_pred, average="macro"),
            "precision_weighted": precision_score(y_test, y_pred, average="weighted"),
            "recall_weighted": recall_score(y_test, y_pred, average="weighted"),
            "f1_weighted": f1_score(y_test, y_pred, average="weighted"),
            "latency_total": latency,
            "latency_per_sample": latency / len(X_test),
        }

        return metrics

    @staticmethod
    def print_evaluation(
        classifier: TriageClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> None:
        """
        Affiche un rapport d'évaluation complet.

        Args:
            classifier: Modèle à évaluer
            X_test: Features de test
            y_test: Labels de test
        """
        print("\n" + "=" * 60)
        print("EVALUATION DU MODELE")
        print("=" * 60)

        # Prédictions
        y_pred, y_proba, latency = classifier.predict(X_test)

        # Noms des classes
        class_names = classifier.preprocessor.get_class_names()
        y_test_labels = classifier.preprocessor.inverse_transform_labels(y_test)
        y_pred_labels = classifier.preprocessor.inverse_transform_labels(y_pred)

        # Rapport de classification
        print("\nRapport de classification :")
        print(classification_report(y_test_labels, y_pred_labels, target_names=class_names))

        # Matrice de confusion
        print("\nMatrice de confusion :")
        cm = confusion_matrix(y_test, y_pred)
        ModelEvaluator._print_confusion_matrix(cm, class_names)

        # Métriques de latence
        print("\nPerformances :")
        print(f"  Latence totale    : {latency:.4f}s")
        print(f"  Latence moyenne   : {latency / len(X_test) * 1000:.2f}ms par patient")
        print(f"  Throughput        : {len(X_test) / latency:.0f} patients/s")

        # Distribution des prédictions
        print("\nDistribution des predictions :")
        unique, counts = np.unique(y_pred_labels, return_counts=True)
        for label, count in zip(unique, counts):
            percentage = count / len(y_pred) * 100
            print(f"  {label:6} : {count:4} patients ({percentage:5.1f}%)")

        print("\n" + "=" * 60)

    @staticmethod
    def _print_confusion_matrix(cm: np.ndarray, class_names: list) -> None:
        """
        Affiche la matrice de confusion de manière lisible.

        Args:
            cm: Matrice de confusion
            class_names: Noms des classes
        """
        # En-tête
        header = "       " + "".join([f"{name:>8}" for name in class_names])
        print(header)
        print("       " + "-" * (8 * len(class_names)))

        # Lignes
        for i, row in enumerate(cm):
            row_str = f"{class_names[i]:6} |"
            for val in row:
                row_str += f"{val:7} "
            print(row_str)

    @staticmethod
    def get_metrics_dict(
        classifier: TriageClassifier,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Dict:
        """
        Retourne un dictionnaire complet des métriques.

        Args:
            classifier: Modèle à évaluer
            X_test: Features de test
            y_test: Labels de test

        Returns:
            Dict: Métriques détaillées
        """
        # Prédictions
        y_pred, y_proba, latency = classifier.predict(X_test)

        # Noms des classes
        class_names = classifier.preprocessor.get_class_names()

        # Métriques par classe
        precision_per_class = precision_score(
            y_test, y_pred, average=None, labels=range(len(class_names))
        )
        recall_per_class = recall_score(
            y_test, y_pred, average=None, labels=range(len(class_names))
        )
        f1_per_class = f1_score(
            y_test, y_pred, average=None, labels=range(len(class_names))
        )

        # Construction du dictionnaire
        metrics = {
            "global": {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision_macro": float(precision_score(y_test, y_pred, average="macro")),
                "recall_macro": float(recall_score(y_test, y_pred, average="macro")),
                "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
                "latency_total": float(latency),
                "latency_per_sample": float(latency / len(X_test)),
            },
            "per_class": {
                class_name: {
                    "precision": float(precision_per_class[i]),
                    "recall": float(recall_per_class[i]),
                    "f1": float(f1_per_class[i]),
                }
                for i, class_name in enumerate(class_names)
            },
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

        return metrics
