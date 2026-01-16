"""
Préprocessing des données pour le modèle de classification.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from sklearn.preprocessing import LabelEncoder, StandardScaler


class TriagePreprocessor:
    """
    Préprocesseur pour les données de triage.

    Gère :
    - Chargement des données CSV
    - Nettoyage et imputation
    - Encodage des variables catégorielles
    - Normalisation des features numériques
    """

    def __init__(self):
        """Initialise le préprocesseur."""
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.feature_columns: Optional[list] = None
        self.is_fitted = False

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Charge les données depuis un fichier CSV.

        Args:
            csv_path: Chemin vers le fichier CSV

        Returns:
            pd.DataFrame: Données chargées
        """
        df = pd.read_csv(csv_path)
        print(f"Dataset charge : {len(df)} patients")
        return df

    def prepare_features(
        self, df: pd.DataFrame, fit: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Prépare les features pour le modèle.

        Args:
            df: DataFrame contenant les données
            fit: Si True, ajuste le scaler et l'encodeur

        Returns:
            Tuple[X, y]: Features et labels (y=None si pas de colonne gravity_level)
        """
        # Copie du dataframe pour ne pas modifier l'original
        df = df.copy()

        # Séparation features / target
        if "gravity_level" in df.columns:
            y = df["gravity_level"].values
            df = df.drop(columns=["gravity_level"])
        else:
            y = None

        # Suppression des colonnes non pertinentes pour la prédiction
        columns_to_drop = [
            "id",
            "motif_consultation",
            "antecedents",
            "traitements_en_cours",
        ]
        df = df.drop(columns=[c for c in columns_to_drop if c in df.columns])

        # Encodage du sexe (M=0, F=1, Autre=2)
        if "sexe" in df.columns:
            df["sexe"] = df["sexe"].map({"M": 0, "F": 1, "Autre": 2})

        # Imputation des valeurs manquantes pour glycemie
        if "glycemie" in df.columns:
            df["glycemie"] = df["glycemie"].fillna(1.0)  # Valeur normale

        # Sauvegarde des colonnes de features (première fois)
        if fit:
            self.feature_columns = df.columns.tolist()

        # Vérification que toutes les colonnes attendues sont présentes
        if self.feature_columns is not None:
            missing_cols = set(self.feature_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Colonnes manquantes : {missing_cols}")

            # Réorganiser les colonnes dans le bon ordre
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
                    "Le préprocesseur n'est pas encore fitté. "
                    "Utilisez fit=True lors du premier appel."
                )
            X = self.scaler.transform(X)

        # Encodage des labels
        if y is not None and fit:
            y = self.label_encoder.fit_transform(y)
        elif y is not None:
            y = self.label_encoder.transform(y)

        return X, y

    def prepare_train_test(
        self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prépare les données pour l'entraînement (train/test split).

        Args:
            df: DataFrame contenant les données
            test_size: Proportion du test set
            random_state: Graine aléatoire

        Returns:
            Tuple[X_train, X_test, y_train, y_test]
        """
        from sklearn.model_selection import train_test_split

        # Préparation des features et labels
        X, y = self.prepare_features(df, fit=True)

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        print(f"Train set : {len(X_train)} patients")
        print(f"Test set  : {len(X_test)} patients")

        return X_train, X_test, y_train, y_test

    def get_feature_names(self) -> list:
        """
        Retourne les noms des features utilisées.

        Returns:
            list: Liste des noms de features
        """
        if self.feature_columns is None:
            raise ValueError("Le préprocesseur n'a pas encore été fitté.")
        return self.feature_columns

    def get_class_names(self) -> list:
        """
        Retourne les noms des classes (niveaux de gravité).

        Returns:
            list: Liste des noms de classes
        """
        if not hasattr(self.label_encoder, "classes_"):
            raise ValueError("Le label encoder n'a pas encore été fitté.")
        return self.label_encoder.classes_.tolist()

    def inverse_transform_labels(self, y_encoded: np.ndarray) -> np.ndarray:
        """
        Convertit les labels encodés en labels originaux.

        Args:
            y_encoded: Labels encodés (entiers)

        Returns:
            np.ndarray: Labels originaux (GRIS/VERT/JAUNE/ROUGE)
        """
        return self.label_encoder.inverse_transform(y_encoded)
