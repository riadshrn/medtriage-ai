# Module de Classification ML

Ce module implemente le classificateur XGBoost pour le triage medical.

## Architecture

```
src/ml/
├── __init__.py
├── preprocessor.py    # Preparation des donnees
├── classifier.py      # Classificateur XGBoost
├── trainer.py         # Pipeline d'entrainement
└── evaluator.py       # Evaluation du modele
```

## Classes

### TriagePreprocessor

Prepare les donnees patients pour l'entrainement ML.

- Encodage du sexe (M=0, F=1)
- Normalisation des constantes vitales
- Imputation des valeurs manquantes (glycemie)
- Extraction des features

### TriageClassifier

Classificateur XGBoost multi-classes (4 niveaux de gravite).

**Hyperparametres par defaut :**
- `n_estimators`: 100
- `max_depth`: 6
- `learning_rate`: 0.1
- `objective`: multi:softmax

**Methodes :**
- `train(X, y)` : Entraine le modele
- `predict(X)` : Predit les classes
- `predict_proba(X)` : Probabilites par classe
- `save(path)` / `load(path)` : Persistence

### ModelTrainer

Pipeline complet d'entrainement avec split train/test.

### ModelEvaluator

Evaluation du modele avec metriques :
- Accuracy
- Precision, Recall, F1-score par classe
- Matrice de confusion

## Tests

```bash
python -m pytest tests/test_ml.py -v
```

### Resultats des tests

| Test | Description | Statut |
|------|-------------|--------|
| test_load_and_prepare | Chargement et preparation des donnees | PASSED |
| test_prepare_features | Extraction des features | PASSED |
| test_sexe_encoding | Encodage du sexe | PASSED |
| test_missing_glycemie_imputation | Imputation glycemie manquante | PASSED |
| test_train | Entrainement du modele | PASSED |
| test_predict | Prediction | PASSED |
| test_save_and_load | Sauvegarde et chargement | PASSED |
| test_evaluate | Evaluation des metriques | PASSED |

**Total : 8 tests - 8 passed**

## Utilisation

```python
from src.ml import TriagePreprocessor, TriageClassifier, ModelTrainer

# Charger et preparer les donnees
preprocessor = TriagePreprocessor()
df = preprocessor.load_and_prepare("data/raw/patients.csv")
X, y = preprocessor.prepare_features(df)

# Entrainer le modele
classifier = TriageClassifier()
classifier.train(X, y)

# Sauvegarder
classifier.save("models/trained/triage_model.json")

# Predire
predictions = classifier.predict(X_new)
probas = classifier.predict_proba(X_new)
```

## Script CLI

```bash
python scripts/train_model.py --data data/raw/patients.csv --output models/trained
```

## Performance

Sur le dataset synthetique de 1000 patients :
- **Accuracy** : ~99%
- **F1-score macro** : ~0.99
