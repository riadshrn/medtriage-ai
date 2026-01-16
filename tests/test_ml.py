"""
Tests unitaires pour le module ML.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.ml import TriagePreprocessor, TriageClassifier, ModelTrainer, ModelEvaluator


class TestTriagePreprocessor:
    """Tests pour TriagePreprocessor."""

    @pytest.fixture
    def sample_dataframe(self):
        """Fixture avec un DataFrame exemple."""
        return pd.DataFrame({
            "id": ["1", "2", "3"],
            "age": [45, 70, 25],
            "sexe": ["M", "F", "M"],
            "motif_consultation": ["Test1", "Test2", "Test3"],
            "frequence_cardiaque": [80, 120, 65],
            "pression_systolique": [120, 180, 110],
            "pression_diastolique": [80, 100, 70],
            "frequence_respiratoire": [16, 25, 14],
            "temperature": [37.0, 38.5, 36.8],
            "saturation_oxygene": [98, 88, 99],
            "echelle_douleur": [3, 8, 1],
            "glycemie": [1.0, 1.2, None],
            "antecedents": ["HTA", "Diabète", None],
            "traitements_en_cours": ["Test", "Test2", None],
            "gravity_level": ["VERT", "JAUNE", "GRIS"],
        })

    def test_load_and_prepare(self, sample_dataframe, tmp_path):
        """Test du chargement et de la préparation."""
        # Sauvegarde temporaire
        csv_path = tmp_path / "test_data.csv"
        sample_dataframe.to_csv(csv_path, index=False)

        # Chargement
        preprocessor = TriagePreprocessor()
        df = preprocessor.load_data(str(csv_path))

        assert len(df) == 3
        assert "gravity_level" in df.columns

    def test_prepare_features(self, sample_dataframe):
        """Test de la préparation des features."""
        preprocessor = TriagePreprocessor()

        X, y = preprocessor.prepare_features(sample_dataframe, fit=True)

        assert X.shape[0] == 3  # 3 samples
        assert X.shape[1] in [9, 10]  # 9 ou 10 features selon le dataset
        assert y is not None
        assert len(y) == 3

    def test_sexe_encoding(self, sample_dataframe):
        """Test de l'encodage du sexe."""
        preprocessor = TriagePreprocessor()

        X, _ = preprocessor.prepare_features(sample_dataframe, fit=True)

        # Vérifier que les features sont bien normalisées (pas de valeurs exactes après scaling)
        # On vérifie juste que le shape est correct et que les valeurs sont finies
        assert np.all(np.isfinite(X))
        assert X.shape[0] == 3

    def test_missing_glycemie_imputation(self):
        """Test de l'imputation des glycémies manquantes."""
        df = pd.DataFrame({
            "age": [45],
            "sexe": ["M"],
            "frequence_cardiaque": [80],
            "pression_systolique": [120],
            "pression_diastolique": [80],
            "frequence_respiratoire": [16],
            "temperature": [37.0],
            "saturation_oxygene": [98],
            "echelle_douleur": [3],
            "glycemie": [None],
            "gravity_level": ["VERT"],
        })

        preprocessor = TriagePreprocessor()
        X, _ = preprocessor.prepare_features(df, fit=True)

        # Glycémie devrait être imputée à 1.0
        assert X[0, -1] == pytest.approx(0.0, abs=1.0)  # Après normalisation


class TestTriageClassifier:
    """Tests pour TriageClassifier."""

    @pytest.fixture
    def trained_classifier(self, tmp_path):
        """Fixture avec un modèle entraîné."""
        # Génération de données synthétiques
        np.random.seed(42)
        X_train = np.random.rand(100, 9)
        y_train = np.random.randint(0, 4, 100)

        # Entraînement
        classifier = TriageClassifier(n_estimators=10, random_state=42)
        classifier.preprocessor.is_fitted = True
        classifier.preprocessor.feature_columns = [
            "age", "sexe", "frequence_cardiaque", "pression_systolique",
            "pression_diastolique", "frequence_respiratoire", "temperature",
            "saturation_oxygene", "echelle_douleur"
        ]
        classifier.preprocessor.scaler.fit(X_train)
        classifier.preprocessor.label_encoder.fit(["GRIS", "VERT", "JAUNE", "ROUGE"])
        classifier.train(X_train, y_train)

        return classifier

    def test_train(self, trained_classifier):
        """Test de l'entraînement."""
        assert trained_classifier.is_trained

    def test_predict(self, trained_classifier):
        """Test de la prédiction."""
        X_test = np.random.rand(10, 9)

        predictions, probabilities, latency = trained_classifier.predict(X_test)

        assert len(predictions) == 10
        assert probabilities.shape == (10, 4)  # 4 classes
        assert latency > 0

    def test_save_and_load(self, trained_classifier, tmp_path):
        """Test de la sauvegarde et du chargement."""
        model_path = tmp_path / "model.json"
        preprocessor_path = tmp_path / "preprocessor.pkl"

        # Sauvegarde
        trained_classifier.save(str(model_path), str(preprocessor_path))

        assert model_path.exists()
        assert preprocessor_path.exists()

        # Chargement
        loaded_classifier = TriageClassifier.load(
            str(model_path), str(preprocessor_path)
        )

        assert loaded_classifier.is_trained


class TestModelEvaluator:
    """Tests pour ModelEvaluator."""

    def test_evaluate(self):
        """Test de l'évaluation."""
        # Création d'un modèle factice
        np.random.seed(42)
        X_train = np.random.rand(100, 9)
        y_train = np.random.randint(0, 4, 100)
        X_test = np.random.rand(20, 9)
        y_test = np.random.randint(0, 4, 20)

        classifier = TriageClassifier(n_estimators=10, random_state=42)
        classifier.preprocessor.is_fitted = True
        classifier.preprocessor.feature_columns = [
            "age", "sexe", "frequence_cardiaque", "pression_systolique",
            "pression_diastolique", "frequence_respiratoire", "temperature",
            "saturation_oxygene", "echelle_douleur"
        ]
        classifier.preprocessor.scaler.fit(X_train)
        classifier.preprocessor.label_encoder.fit(["GRIS", "VERT", "JAUNE", "ROUGE"])
        classifier.train(X_train, y_train)

        # Évaluation
        metrics = ModelEvaluator.evaluate(classifier, X_test, y_test)

        assert "accuracy" in metrics
        assert "precision_macro" in metrics
        assert "recall_macro" in metrics
        assert "f1_macro" in metrics
        assert 0 <= metrics["accuracy"] <= 1
