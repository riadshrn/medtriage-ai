"""
Preprocessing des donnees pour le modele de classification.

Utilise feature_config.py comme source unique de verite pour les features.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, List
from sklearn.preprocessing import LabelEncoder, StandardScaler
import logging

from .feature_config import (
    ALL_ML_FEATURES,
    COLUMNS_TO_DROP,
    DEFAULT_VALUES,
    SEXE_ENCODING,
    assess_prediction_quality,
    PredictionQuality,
)

logger = logging.getLogger(__name__)


class TriagePreprocessor:
    """
    Preprocesseur pour les donnees de triage.

    Gere :
    - Chargement des donnees CSV
    - Nettoyage et imputation
    - Encodage des variables categorielles
    - Normalisation des features numeriques
    """

    def __init__(self):
        """Initialise le preprocesseur."""
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.feature_columns: Optional[List[str]] = None
        self.is_fitted = False

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Charge les donnees depuis un fichier CSV.

        Args:
            csv_path: Chemin vers le fichier CSV

        Returns:
            pd.DataFrame: Donnees chargees
        """
        df = pd.read_csv(csv_path)
        logger.info(f"Dataset charge : {len(df)} patients")
        return df

    def prepare_features(
        self, df: pd.DataFrame, fit: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Prepare les features pour le modele.

        Args:
            df: DataFrame contenant les donnees
            fit: Si True, ajuste le scaler et l'encodeur

        Returns:
            Tuple[X, y]: Features et labels (y=None si pas de colonne gravity_level)
        """
        df = df.copy()

        # Separation features / target
        if "gravity_level" in df.columns:
            y = df["gravity_level"].values
            df = df.drop(columns=["gravity_level"])
        else:
            y = None

        # Suppression des colonnes non pertinentes (utilise feature_config)
        df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])

        # Encodage du sexe (M=0, F=1, Autre=2)
        if "sexe" in df.columns:
            df["sexe"] = df["sexe"].map(SEXE_ENCODING).fillna(SEXE_ENCODING["Autre"])

        # Imputation des valeurs manquantes avec les valeurs par defaut
        for feature, default_val in DEFAULT_VALUES.items():
            if feature in df.columns:
                df[feature] = df[feature].fillna(default_val)

        # Sauvegarde des colonnes de features (premiere fois)
        if fit:
            # Utilise l'ordre defini dans feature_config, mais seulement les colonnes presentes
            self.feature_columns = [f for f in ALL_ML_FEATURES if f in df.columns]
            logger.info(f"Features utilisees: {self.feature_columns}")

        # Verification que toutes les colonnes attendues sont presentes
        if self.feature_columns is not None:
            missing_cols = set(self.feature_columns) - set(df.columns)
            if missing_cols:
                # Ajouter les colonnes manquantes avec valeurs par defaut
                for col in missing_cols:
                    if col in DEFAULT_VALUES:
                        df[col] = DEFAULT_VALUES[col]
                        logger.warning(f"Colonne {col} ajoutee avec valeur par defaut {DEFAULT_VALUES[col]}")
                    else:
                        raise ValueError(f"Colonne manquante sans valeur par defaut: {col}")

            # Reorganiser les colonnes dans le bon ordre
            df = df[self.feature_columns]

        # Conversion en array numpy
        X = df.values.astype(float)

        # Normalisation des features
        if fit:
            X = self.scaler.fit_transform(X)
            self.is_fitted = True
        else:
            if not self.is_fitted:
                raise ValueError(
                    "Le preprocesseur n'est pas encore fitte. "
                    "Utilisez fit=True lors du premier appel."
                )
            X = self.scaler.transform(X)

        # Encodage des labels
        if y is not None and fit:
            y = self.label_encoder.fit_transform(y)
        elif y is not None:
            y = self.label_encoder.transform(y)

        return X, y

    def prepare_single_patient(
        self, features: Dict[str, any]
    ) -> Tuple[np.ndarray, PredictionQuality, List[str]]:
        """
        Prepare les features pour un seul patient (inference).

        Args:
            features: Dictionnaire des features du patient

        Returns:
            Tuple (X, qualite_prediction, features_manquantes)
        """
        if not self.is_fitted:
            raise ValueError("Le preprocesseur n'est pas encore fitte.")

        # Evaluer la qualite des donnees
        quality, missing = assess_prediction_quality(features)

        # Encoder le sexe si present
        processed = features.copy()
        if "sexe" in processed and isinstance(processed["sexe"], str):
            processed["sexe"] = SEXE_ENCODING.get(processed["sexe"], SEXE_ENCODING["Autre"])

        # Imputer les valeurs manquantes
        for feature in self.feature_columns:
            if feature not in processed or processed[feature] is None:
                if feature in DEFAULT_VALUES:
                    processed[feature] = DEFAULT_VALUES[feature]
                    logger.debug(f"Feature {feature} imputee avec {DEFAULT_VALUES[feature]}")

        # Creer le DataFrame dans le bon ordre
        df = pd.DataFrame([{f: processed.get(f) for f in self.feature_columns}])
        X = df.values.astype(float)

        # Normaliser
        X = self.scaler.transform(X)

        return X, quality, missing

    def prepare_train_test(
        self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare les donnees pour l'entrainement (train/test split).

        Args:
            df: DataFrame contenant les donnees
            test_size: Proportion du test set
            random_state: Graine aleatoire

        Returns:
            Tuple[X_train, X_test, y_train, y_test]
        """
        from sklearn.model_selection import train_test_split

        # Preparation des features et labels
        X, y = self.prepare_features(df, fit=True)

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        logger.info(f"Train set : {len(X_train)} patients")
        logger.info(f"Test set  : {len(X_test)} patients")

        return X_train, X_test, y_train, y_test

    def get_feature_names(self) -> List[str]:
        """
        Retourne les noms des features utilisees.

        Returns:
            list: Liste des noms de features
        """
        if self.feature_columns is None:
            raise ValueError("Le preprocesseur n'a pas encore ete fitte.")
        return self.feature_columns.copy()

    def get_class_names(self) -> List[str]:
        """
        Retourne les noms des classes (niveaux de gravite).

        Returns:
            list: Liste des noms de classes
        """
        if not hasattr(self.label_encoder, "classes_"):
            raise ValueError("Le label encoder n'a pas encore ete fitte.")
        return self.label_encoder.classes_.tolist()

    def inverse_transform_labels(self, y_encoded: np.ndarray) -> np.ndarray:
        """
        Convertit les labels encodes en labels originaux.

        Args:
            y_encoded: Labels encodes (entiers)

        Returns:
            np.ndarray: Labels originaux (GRIS/VERT/JAUNE/ROUGE)
        """
        return self.label_encoder.inverse_transform(y_encoded)
