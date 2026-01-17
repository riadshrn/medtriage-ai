"""
Service d'entraînement des modèles avec MLflow

Ce service gère :
- Le réentraînement sur les données de feedback
- L'intégration des datasets Hugging Face
- Le tracking avec MLflow
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TrainingService:
    """
    Service d'entraînement et de gestion des modèles ML

    Fonctionnalités :
    - Réentraînement sur données de feedback
    - Intégration datasets Hugging Face
    - Tracking MLflow
    - Versioning des modèles
    """

    def __init__(self):
        self.mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///./data/mlflow.db")
        self.experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "redflag-triage")
        self._mlflow = None

    def _init_mlflow(self):
        """Initialise MLflow"""
        if self._mlflow is None:
            try:
                import mlflow
                mlflow.set_tracking_uri(self.mlflow_tracking_uri)
                mlflow.set_experiment(self.experiment_name)
                self._mlflow = mlflow
                print(f"MLflow initialisé: {self.mlflow_tracking_uri}")
            except Exception as e:
                print(f"Erreur MLflow: {e}")

    def load_feedback_data(self, db_session) -> pd.DataFrame:
        """
        Charge les données de feedback validées depuis la base

        Returns:
            DataFrame avec les colonnes nécessaires pour l'entraînement
        """
        from src.api.core.database import TriagePrediction

        predictions = db_session.query(TriagePrediction).filter(
            TriagePrediction.validated == True
        ).all()

        data = []
        for p in predictions:
            data.append({
                'age': p.patient_age,
                'sexe': p.patient_sexe,
                'frequence_cardiaque': p.frequence_cardiaque,
                'frequence_respiratoire': p.frequence_respiratoire,
                'saturation_oxygene': p.saturation_oxygene,
                'pression_systolique': p.pression_systolique,
                'pression_diastolique': p.pression_diastolique,
                'temperature': p.temperature,
                'echelle_douleur': p.echelle_douleur,
                'gravity_level': p.validated_level  # Label validé par l'infirmière
            })

        return pd.DataFrame(data)

    def load_hf_datasets(self) -> pd.DataFrame:
        """
        Charge et prépare les datasets Hugging Face

        Datasets utilisés :
        - miriad/miriad-4.4M : Cas médicaux variés
        - mlabonne/medical-cases-fr : Cas médicaux en français
        """
        try:
            from datasets import load_dataset

            all_data = []

            # Dataset medical-cases-fr
            try:
                print("Chargement de mlabonne/medical-cases-fr...")
                ds = load_dataset("mlabonne/medical-cases-fr", split="train[:1000]")

                for item in ds:
                    # Adapter les données au format attendu
                    # Ce dataset a des cas médicaux en français
                    processed = self._process_medical_case_fr(item)
                    if processed:
                        all_data.append(processed)

                print(f"  -> {len(all_data)} cas chargés")
            except Exception as e:
                print(f"Erreur chargement medical-cases-fr: {e}")

            return pd.DataFrame(all_data) if all_data else pd.DataFrame()

        except ImportError:
            print("Package 'datasets' non installé. pip install datasets")
            return pd.DataFrame()

    def _process_medical_case_fr(self, item: dict) -> Optional[dict]:
        """
        Transforme un cas médical du dataset HF en format d'entraînement

        Note: Cette fonction doit être adaptée selon la structure réelle du dataset
        """
        try:
            # Extraire les informations du cas
            # Structure hypothétique - à adapter selon le dataset réel
            text = item.get("text", "")

            # Générer des constantes simulées basées sur le texte
            # En production, il faudrait un modèle NER pour extraire les vraies valeurs
            import random

            # Détecter la gravité à partir du texte
            gravity = self._detect_gravity_from_text(text)

            return {
                'age': random.randint(20, 80),
                'sexe': random.choice(['M', 'F']),
                'frequence_cardiaque': self._generate_constante_for_gravity(gravity, 'fc'),
                'frequence_respiratoire': self._generate_constante_for_gravity(gravity, 'fr'),
                'saturation_oxygene': self._generate_constante_for_gravity(gravity, 'spo2'),
                'pression_systolique': self._generate_constante_for_gravity(gravity, 'pas'),
                'pression_diastolique': self._generate_constante_for_gravity(gravity, 'pad'),
                'temperature': self._generate_constante_for_gravity(gravity, 'temp'),
                'echelle_douleur': self._generate_constante_for_gravity(gravity, 'douleur'),
                'gravity_level': gravity
            }
        except Exception:
            return None

    def _detect_gravity_from_text(self, text: str) -> str:
        """Détecte le niveau de gravité à partir du texte"""
        text_lower = text.lower()

        # Mots-clés par gravité
        rouge_keywords = ["urgence vitale", "arrêt cardiaque", "coma", "hémorragie massive",
                          "détresse respiratoire", "choc", "inconscient"]
        jaune_keywords = ["fracture", "douleur intense", "fièvre élevée", "vomissements",
                          "infection", "blessure", "plaie profonde"]
        vert_keywords = ["entorse", "contusion", "grippe", "toux", "mal de gorge",
                         "douleur légère", "brûlure légère"]

        if any(kw in text_lower for kw in rouge_keywords):
            return "ROUGE"
        elif any(kw in text_lower for kw in jaune_keywords):
            return "JAUNE"
        elif any(kw in text_lower for kw in vert_keywords):
            return "VERT"
        else:
            return "GRIS"

    def _generate_constante_for_gravity(self, gravity: str, constante: str) -> float:
        """Génère une constante vitale cohérente avec le niveau de gravité"""
        import random

        ranges = {
            "ROUGE": {
                'fc': (130, 200), 'fr': (30, 50), 'spo2': (70, 88),
                'pas': (50, 80), 'pad': (30, 50), 'temp': (39, 42), 'douleur': (8, 10)
            },
            "JAUNE": {
                'fc': (100, 130), 'fr': (22, 30), 'spo2': (88, 94),
                'pas': (80, 100), 'pad': (50, 65), 'temp': (38, 39), 'douleur': (5, 8)
            },
            "VERT": {
                'fc': (70, 100), 'fr': (14, 22), 'spo2': (94, 98),
                'pas': (100, 130), 'pad': (65, 85), 'temp': (36.5, 38), 'douleur': (2, 5)
            },
            "GRIS": {
                'fc': (60, 80), 'fr': (12, 18), 'spo2': (97, 100),
                'pas': (110, 130), 'pad': (70, 85), 'temp': (36, 37.5), 'douleur': (0, 2)
            }
        }

        r = ranges.get(gravity, ranges["VERT"])
        low, high = r.get(constante, (50, 100))
        return round(random.uniform(low, high), 1)

    def train_model(
        self,
        data: pd.DataFrame,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Entraîne un nouveau modèle sur les données fournies

        Args:
            data: DataFrame avec les features et le label 'gravity_level'
            hyperparameters: Paramètres XGBoost personnalisés

        Returns:
            Dict avec les métriques et infos du modèle
        """
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        import xgboost as xgb
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        import pickle

        # Paramètres par défaut
        default_params = {
            'n_estimators': 150,
            'max_depth': 8,
            'learning_rate': 0.1,
            'objective': 'multi:softprob',
            'num_class': 4,
            'eval_metric': 'mlogloss'
        }
        params = {**default_params, **(hyperparameters or {})}

        # Préparer les données
        X = data.drop('gravity_level', axis=1)
        y = data['gravity_level']

        # Encoder les labels
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Préprocesseur
        numeric_features = ['age', 'frequence_cardiaque', 'frequence_respiratoire',
                           'saturation_oxygene', 'pression_systolique', 'pression_diastolique',
                           'temperature', 'echelle_douleur']

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', 'passthrough', ['sexe'])
            ]
        )

        # Encoder le sexe
        X_train_copy = X_train.copy()
        X_test_copy = X_test.copy()
        X_train_copy['sexe'] = X_train_copy['sexe'].map({'M': 0, 'F': 1})
        X_test_copy['sexe'] = X_test_copy['sexe'].map({'M': 0, 'F': 1})

        # Fit preprocessor
        X_train_processed = preprocessor.fit_transform(X_train_copy)
        X_test_processed = preprocessor.transform(X_test_copy)

        # Entraîner
        model = xgb.XGBClassifier(**params)
        model.fit(X_train_processed, y_train)

        # Évaluer
        y_pred = model.predict(X_test_processed)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }

        # Sauvegarder
        version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        model_path = f"models/trained/triage_model_{version}.json"
        preprocessor_path = f"models/trained/preprocessor_{version}.pkl"

        os.makedirs("models/trained", exist_ok=True)
        model.save_model(model_path)
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(preprocessor, f)

        # Log MLflow
        run_id = None
        try:
            self._init_mlflow()
            if self._mlflow:
                with self._mlflow.start_run() as run:
                    self._mlflow.log_params(params)
                    self._mlflow.log_metrics(metrics)
                    self._mlflow.log_artifact(model_path)
                    self._mlflow.log_artifact(preprocessor_path)
                    run_id = run.info.run_id
        except Exception as e:
            print(f"Erreur logging MLflow: {e}")

        return {
            'version': version,
            'model_path': model_path,
            'preprocessor_path': preprocessor_path,
            'metrics': metrics,
            'mlflow_run_id': run_id,
            'training_samples': len(data)
        }
