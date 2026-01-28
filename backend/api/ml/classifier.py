"""
Modèle de classification pour le triage des patients.
"""

import pickle
import time
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
from xgboost import XGBClassifier

from .preprocessor import TriagePreprocessor


class TriageClassifier:
    """
    Wrapper pour le modèle de classification XGBoost.

    Gère :
    - Entraînement du modèle
    - Prédictions avec probabilités
    - Sauvegarde/chargement du modèle
    - Mesure de la latence
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42,
    ):
        """
        Initialise le classificateur.

        Args:
            n_estimators: Nombre d'arbres
            max_depth: Profondeur maximale des arbres
            learning_rate: Taux d'apprentissage
            random_state: Graine aléatoire
        """
        self.model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            eval_metric="mlogloss",
            use_label_encoder=False,
        )
        self.preprocessor = TriagePreprocessor()
        self.is_trained = False

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Entraîne le modèle.

        Args:
            X_train: Features d'entraînement
            y_train: Labels d'entraînement
        """
        print("Entrainement du modele XGBoost...")
        start_time = time.time()

        self.model.fit(X_train, y_train)

        elapsed_time = time.time() - start_time
        print(f"Entrainement termine en {elapsed_time:.2f}s")

        self.is_trained = True

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Prédit les classes et les probabilités.

        Args:
            X: Features à prédire

        Returns:
            Tuple[predictions, probabilities, latency]:
                - predictions: Classes prédites (encodées)
                - probabilities: Probabilités pour chaque classe
                - latency: Temps de prédiction (en secondes)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas encore entraîné.")

        start_time = time.time()

        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        latency = time.time() - start_time

        return predictions, probabilities, latency

    def predict_single(
        self, features: dict
    ) -> Tuple[str, float, dict, float]:
        """
        Prédit la classe pour un seul patient.

        Args:
            features: Dictionnaire des features du patient

        Returns:
            Tuple[gravity_level, confidence, probabilities, latency]:
                - gravity_level: Niveau de gravité prédit (GRIS/VERT/JAUNE/ROUGE)
                - confidence: Score de confiance (0-1)
                - probabilities: Dict des probabilités pour chaque classe
                - latency: Temps de prédiction (en secondes)
        """
        # Conversion en DataFrame pour le préprocesseur
        import pandas as pd

        df = pd.DataFrame([features])

        # Préparation des features
        X, _ = self.preprocessor.prepare_features(df, fit=False)

        # Prédiction
        pred, proba, latency = self.predict(X)

        # Décodage du label
        gravity_level = self.preprocessor.inverse_transform_labels(pred)[0]

        # Score de confiance (probabilité de la classe prédite)
        confidence = float(np.max(proba[0]))

        # Dictionnaire des probabilités
        class_names = self.preprocessor.get_class_names()
        probabilities = {
            class_name: float(prob)
            for class_name, prob in zip(class_names, proba[0])
        }

        return gravity_level, confidence, probabilities, latency

    def save(self, model_path: str, preprocessor_path: str) -> None:
        """
        Sauvegarde le modèle et le préprocesseur.

        Args:
            model_path: Chemin de sauvegarde du modèle
            preprocessor_path: Chemin de sauvegarde du préprocesseur
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas encore entraîné.")

        # Création des dossiers si nécessaire
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        Path(preprocessor_path).parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarde du modèle XGBoost
        self.model.save_model(model_path)

        # Sauvegarde du préprocesseur
        with open(preprocessor_path, "wb") as f:
            pickle.dump(self.preprocessor, f)

        print(f"Modele sauvegarde : {model_path}")
        print(f"Preprocesseur sauvegarde : {preprocessor_path}")

    @classmethod
    def load(cls, model_path: str, preprocessor_path: str) -> "TriageClassifier":
        """
        Charge un modèle et son préprocesseur depuis le disque.

        Args:
            model_path: Chemin du modèle
            preprocessor_path: Chemin du préprocesseur

        Returns:
            TriageClassifier: Instance du classificateur chargé
        """
        # Création d'une instance vide
        classifier = cls()

        # Chargement du modèle XGBoost
        classifier.model.load_model(model_path)

        # Chargement du préprocesseur
        with open(preprocessor_path, "rb") as f:
            classifier.preprocessor = pickle.load(f)

        classifier.is_trained = True

        print(f"Modele charge : {model_path}")
        print(f"Preprocesseur charge : {preprocessor_path}")

        return classifier

    def get_feature_importance(self) -> dict:
        """
        Retourne l'importance des features.

        Returns:
            dict: Dictionnaire {feature_name: importance}
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas encore entraîné.")

        feature_names = self.preprocessor.get_feature_names()
        importances = self.model.feature_importances_

        return {
            name: float(importance)
            for name, importance in zip(feature_names, importances)
        }
