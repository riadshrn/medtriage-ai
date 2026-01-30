# Pipeline ML Robuste avec MLflow

> Documentation des améliorations apportées au pipeline ML de MedTriage-AI

## Table des Matières

1. [Résumé des Changements](#résumé-des-changements)
2. [Phase 1: Alignement des Features](#phase-1-alignement-des-features)
3. [Phase 2: Intégration MLflow](#phase-2-intégration-mlflow)
4. [Phase 3: Système de Feedback](#phase-3-système-de-feedback)
5. [Phase 4: Réentraînement](#phase-4-réentraînement)
6. [Architecture Finale](#architecture-finale)
7. [Guide d'Utilisation](#guide-dutilisation)

---

## Résumé des Changements

### Problèmes Résolus

| Problème | Solution |
|----------|----------|
| **Mismatch glycemie** | `triage_service.py` envoie maintenant glycemie au modèle |
| **Valeurs par défaut masquant les erreurs** | Ajout de `prediction_quality` pour indiquer la fiabilité |
| **Erreurs ML silencieuses** | Logging structuré avec `ml_error` et `ml_available` |
| **Pas de versioning modèle** | Intégration MLflow Model Registry |
| **Pas de feedback loop** | API de feedback + réentraînement manuel |

### Fichiers Créés

```
src/api/ml/
├── feature_config.py      # Configuration canonique des features
├── mlflow_config.py       # Setup MLflow
└── feedback_handler.py    # Gestion du feedback

src/api/schemas/
└── feedback.py            # Schémas Pydantic pour feedback

src/api/routes/
└── feedback.py            # Endpoints API feedback

src/api/scripts/
└── retrain_with_feedback.py  # Script de réentraînement
```

### Fichiers Modifiés

```
src/api/ml/preprocessor.py     # Utilise feature_config
src/api/ml/trainer.py          # MLflow tracking
src/api/services/triage_service.py  # Glycemie + logging
src/api/schemas/triage.py      # Nouveaux champs réponse
src/api/main.py                # Router feedback
docker-compose.yml             # Service MLflow
requirements/requirements-api.txt  # mlflow, matplotlib
```

---

## Phase 1: Alignement des Features

### Configuration Canonique (`feature_config.py`)

Source unique de vérité pour les features ML:

```python
# Features requises (doivent être présentes)
REQUIRED_FEATURES = [
    "age", "sexe", "frequence_cardiaque", "pression_systolique",
    "pression_diastolique", "frequence_respiratoire",
    "temperature", "saturation_oxygene"
]

# Features importantes (peuvent être imputées)
IMPORTANT_FEATURES = ["echelle_douleur", "glasgow"]

# Features optionnelles
OPTIONAL_FEATURES = ["glycemie"]

# Valeurs par défaut pour imputation
DEFAULT_VALUES = {
    "age": 45,
    "frequence_cardiaque": 80,
    "glycemie": 1.0,
    "glasgow": 15,
    # ...
}
```

### Qualité de Prédiction

Le système évalue maintenant la qualité des données avant prédiction:

```python
class PredictionQuality(Enum):
    HIGH = "high"           # Toutes features critiques présentes
    MEDIUM = "medium"       # Critiques OK, importantes manquantes
    LOW = "low"             # Features critiques manquantes
    INSUFFICIENT = "insufficient"  # Prédiction non fiable
```

### Nouvelle Réponse API

```json
{
  "prediction_id": "abc123",
  "gravity_level": "JAUNE",
  "confidence_score": 0.85,
  "prediction_quality": "high",
  "missing_features": [],
  "ml_available": true,
  "ml_error": null
}
```

---

## Phase 2: Intégration MLflow

### Architecture MLflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  trainer.py     │────▶│  MLflow Server  │────▶│  Model Registry │
│  (Training)     │     │  (Tracking)     │     │  (Versions)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Experiments    │
                        │  - Métriques    │
                        │  - Paramètres   │
                        │  - Artefacts    │
                        └─────────────────┘
```

### Docker Compose

```yaml
services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.10.0
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlflow/mlruns
      - ./mlartifacts:/mlflow/mlartifacts
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri sqlite:///mlflow/mlruns/mlflow.db
      --default-artifact-root /mlflow/mlartifacts

  api:
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - mlflow
```

### Métriques Trackées

| Métrique | Description |
|----------|-------------|
| `accuracy` | Précision globale |
| `f1_macro` | F1-score macro |
| `precision_macro` | Précision macro |
| `recall_macro` | Rappel macro |
| `cv_accuracy_mean` | Moyenne validation croisée |
| `latency_per_sample_ms` | Temps par prédiction |

### Artefacts Sauvegardés

- `model/` - Modèle XGBoost (format MLflow)
- `preprocessor/preprocessor.pkl` - Préprocesseur sklearn
- `config/feature_config.json` - Configuration features
- `confusion_matrix.png` - Matrice de confusion

---

## Phase 3: Système de Feedback

### Schéma de Feedback

```python
class NurseFeedback(BaseModel):
    prediction_id: str          # ID de la prédiction
    nurse_id: Optional[str]     # ID anonyme infirmière

    original_gravity: str       # Niveau prédit
    feedback_type: FeedbackType # correct/upgrade/downgrade/disagree
    corrected_gravity: str      # Niveau corrigé

    reason: Optional[str]       # Raison de la correction
    missed_symptoms: List[str]  # Symptômes manqués
    patient_features: dict      # Features pour réentraînement
```

### Types de Feedback

| Type | Description | Usage |
|------|-------------|-------|
| `correct` | Prédiction correcte | Validation |
| `upgrade` | Sous-estimation (ex: VERT → JAUNE) | Réentraînement |
| `downgrade` | Sur-estimation (ex: JAUNE → VERT) | Réentraînement |
| `disagree` | Complètement faux | Réentraînement |

### Endpoints API

```
POST /feedback/submit     # Soumettre un feedback
GET  /feedback/stats      # Statistiques agrégées
GET  /feedback/count      # Nombre total de feedbacks
POST /feedback/retrain    # Déclencher réentraînement
```

### Exemple de Soumission

```bash
curl -X POST http://localhost:8000/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "abc123",
    "original_gravity": "VERT",
    "feedback_type": "upgrade",
    "corrected_gravity": "JAUNE",
    "reason": "Détresse respiratoire non détectée",
    "missed_symptoms": ["dyspnée", "tirage"],
    "patient_features": {
      "age": 65,
      "sexe": "M",
      "frequence_cardiaque": 95,
      "saturation_oxygene": 92
    }
  }'
```

### Stockage des Feedbacks

Les feedbacks sont stockés en format JSONL (une ligne JSON par feedback):

```
data/feedback/nurse_feedback.jsonl
```

---

## Phase 4: Réentraînement

### Flux de Réentraînement

```
┌─────────────────┐
│ Données         │
│ Originales      │──────┐
│ (synthetic.csv) │      │
└─────────────────┘      │
                         ▼
┌─────────────────┐  ┌─────────────────┐
│ Feedbacks       │─▶│ Dataset         │
│ (corrections)   │  │ Combiné         │
└─────────────────┘  └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ ModelTrainer    │
                    │ + MLflow        │
                    └────────┬────────┘
                              │
                    ┌─────────▼─────────┐
                    │                   │
              ┌─────▼─────┐    ┌────────▼────────┐
              │ Local     │    │ MLflow          │
              │ Files     │    │ Model Registry  │
              └───────────┘    └─────────────────┘
```

### Script de Réentraînement

```bash
# Réentraînement avec feedbacks (minimum 50)
python src/api/scripts/retrain_with_feedback.py

# Sans feedbacks (données originales uniquement)
python src/api/scripts/retrain_with_feedback.py --no-feedback

# Avec hyperparameter tuning
python src/api/scripts/retrain_with_feedback.py --tune

# Options personnalisées
python src/api/scripts/retrain_with_feedback.py \
  --data data/raw/patients_synthetic.csv \
  --min-feedback 100 \
  --n-estimators 200 \
  --max-depth 8 \
  --run-name "retrain-v2"
```

### Via API

```bash
curl -X POST http://localhost:8000/feedback/retrain \
  -H "Content-Type: application/json" \
  -d '{
    "include_feedback": true,
    "min_feedback_samples": 50,
    "run_name": "api-retrain-2024"
  }'
```

### Seuils de Déclenchement

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `RETRAINING_THRESHOLD` | 100 | Minimum feedbacks avant alerte |
| `ERROR_RATE_THRESHOLD` | 15% | Seuil d'erreur pour recommandation |
| `min_feedback_samples` | 50 | Minimum pour réentraînement |

---

## Architecture Finale

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐ │
│  │ Streamlit │───▶│  FastAPI  │───▶│  MLflow   │    │   Data    │ │
│  │    UI     │    │    API    │    │  Server   │    │  Storage  │ │
│  │  :8501    │    │  :8000    │    │  :5000    │    │           │ │
│  └───────────┘    └─────┬─────┘    └───────────┘    └───────────┘ │
│                         │                                          │
├─────────────────────────┼──────────────────────────────────────────┤
│                         │         ML PIPELINE                      │
│                         ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    TriageService                            │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │  │
│  │  │   FRENCH    │   │  XGBoost    │   │  Quality    │       │  │
│  │  │   Rules     │   │  Classifier │   │  Assessor   │       │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Feedback Loop                            │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │  │
│  │  │  Feedback   │──▶│  Handler    │──▶│  Trainer    │       │  │
│  │  │  API        │   │  (Storage)  │   │  (MLflow)   │       │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Guide d'Utilisation

### 1. Démarrage

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les services
docker-compose ps
```

- **API**: http://localhost:8000
- **MLflow UI**: http://localhost:5000
- **Streamlit**: http://localhost:8501

### 2. Premier Entraînement

```bash
# Entraîner le modèle initial
python src/api/scripts/train_model.py \
  --data data/raw/patients_synthetic.csv \
  --output models/trained
```

### 3. Utilisation en Production

```bash
# Faire une prédiction
curl -X POST http://localhost:8000/triage/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 65,
    "sexe": "M",
    "motif_consultation": "Douleur thoracique",
    "constantes": {
      "frequence_cardiaque": 95,
      "pression_systolique": 140,
      "pression_diastolique": 90,
      "frequence_respiratoire": 20,
      "temperature": 37.2,
      "saturation_oxygene": 96,
      "echelle_douleur": 6
    }
  }'
```

### 4. Cycle de Feedback

```bash
# 1. Obtenir les stats actuelles
curl http://localhost:8000/feedback/stats

# 2. Soumettre des feedbacks (via UI ou API)

# 3. Vérifier le nombre de feedbacks
curl http://localhost:8000/feedback/count

# 4. Réentraîner quand suffisant
curl -X POST http://localhost:8000/feedback/retrain
```

### 5. Gestion des Modèles (MLflow)

Accéder à http://localhost:5000 pour:
- Voir les expériences d'entraînement
- Comparer les métriques entre runs
- Promouvoir un modèle en production
- Télécharger les artefacts

---

## Variables d'Environnement

```env
# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_EXPERIMENT_NAME=medtriage-classification
MLFLOW_MODEL_NAME=triage-classifier

# LLM (pour extraction)
OPENAI_API_KEY=sk-...
# ou
MISTRAL_API_KEY=...
```

---

## Prochaines Étapes Possibles

1. **Interface Streamlit pour feedback** - Boutons de correction dans l'UI
2. **Réentraînement automatique** - Quand taux d'erreur > seuil
3. **A/B Testing** - Comparaison modèles en production
4. **Alertes** - Notification quand performance se dégrade
5. **RAG** - Enrichissement avec base de connaissances médicales

---

*Documentation générée le 26/01/2026*
