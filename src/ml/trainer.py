"""
Entraînement du modèle de classification.
"""

import numpy as np
from typing import Optional
from sklearn.model_selection import cross_val_score

from .classifier import TriageClassifier
from .preprocessor import TriagePreprocessor


class ModelTrainer:
    """
    Gère l'entraînement du modèle de classification.

    Inclut :
    - Split train/test
    - Validation croisée
    - Hyperparameter tuning (optionnel)
    """

    def __init__(self, random_state: int = 42):
        """
        Initialise le trainer.

        Args:
            random_state: Graine aléatoire
        """
        self.random_state = random_state
        self.classifier: Optional[TriageClassifier] = None
        self.preprocessor = TriagePreprocessor()

    def train_from_csv(
        self,
        csv_path: str,
        test_size: float = 0.2,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        cv_folds: int = 5,
    ) -> TriageClassifier:
        """
        Entraîne le modèle depuis un fichier CSV.

        Args:
            csv_path: Chemin vers le CSV de données
            test_size: Proportion du test set
            n_estimators: Nombre d'arbres XGBoost
            max_depth: Profondeur maximale des arbres
            learning_rate: Taux d'apprentissage
            cv_folds: Nombre de folds pour la validation croisée

        Returns:
            TriageClassifier: Modèle entraîné
        """
        print("=" * 60)
        print("ENTRAINEMENT DU MODELE DE CLASSIFICATION")
        print("=" * 60)

        # Chargement des données
        df = self.preprocessor.load_data(csv_path)

        # Préparation train/test
        X_train, X_test, y_train, y_test = self.preprocessor.prepare_train_test(
            df, test_size=test_size, random_state=self.random_state
        )

        # Création du classificateur
        self.classifier = TriageClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=self.random_state,
        )

        # Copie du préprocesseur fitté
        self.classifier.preprocessor = self.preprocessor

        # Validation croisée sur le train set
        if cv_folds > 1:
            print(f"\nValidation croisee ({cv_folds} folds)...")
            cv_scores = cross_val_score(
                self.classifier.model,
                X_train,
                y_train,
                cv=cv_folds,
                scoring="accuracy",
            )
            print(f"Accuracy CV : {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Entraînement sur tout le train set
        print("\nEntrainement sur le train set...")
        self.classifier.train(X_train, y_train)

        # Évaluation sur le test set
        print("\nEvaluation sur le test set...")
        y_pred, y_proba, latency = self.classifier.predict(X_test)

        from sklearn.metrics import accuracy_score

        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy test : {accuracy:.4f}")
        print(f"Latence moyenne : {latency / len(X_test) * 1000:.2f}ms par patient")

        # Affichage de l'importance des features
        print("\nImportance des features :")
        feature_importance = self.classifier.get_feature_importance()
        sorted_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )
        for feature, importance in sorted_features[:10]:
            print(f"  {feature:25} : {importance:.4f}")

        print("\n" + "=" * 60)
        print("ENTRAINEMENT TERMINE")
        print("=" * 60)

        return self.classifier

    def train_with_tuning(
        self,
        csv_path: str,
        test_size: float = 0.2,
        cv_folds: int = 3,
    ) -> TriageClassifier:
        """
        Entraîne le modèle avec recherche d'hyperparamètres.

        Args:
            csv_path: Chemin vers le CSV de données
            test_size: Proportion du test set
            cv_folds: Nombre de folds pour la recherche

        Returns:
            TriageClassifier: Modèle entraîné avec les meilleurs hyperparamètres
        """
        from sklearn.model_selection import RandomizedSearchCV

        print("=" * 60)
        print("ENTRAINEMENT AVEC HYPERPARAMETER TUNING")
        print("=" * 60)

        # Chargement des données
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

        # Modèle de base
        base_model = TriageClassifier(random_state=self.random_state).model

        # Recherche aléatoire
        print("\nRecherche d'hyperparametres (cela peut prendre quelques minutes)...")
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

        print(f"\nMeilleurs parametres : {random_search.best_params_}")
        print(f"Meilleur score CV : {random_search.best_score_:.4f}")

        # Création du classificateur avec les meilleurs paramètres
        self.classifier = TriageClassifier(**random_search.best_params_)
        self.classifier.preprocessor = self.preprocessor
        self.classifier.model = random_search.best_estimator_
        self.classifier.is_trained = True

        # Évaluation sur le test set
        print("\nEvaluation sur le test set...")
        y_pred, _, _ = self.classifier.predict(X_test)

        from sklearn.metrics import accuracy_score

        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy test : {accuracy:.4f}")

        print("\n" + "=" * 60)
        print("ENTRAINEMENT TERMINE")
        print("=" * 60)

        return self.classifier
