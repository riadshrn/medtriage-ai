# Module Agent de Triage

Agent intelligent qui orchestre le système complet de triage des patients.

## Composants

### `TriageAgent`

Agent principal qui coordonne :
1. **Prédiction ML** : Classification du niveau de gravité (XGBoost)
2. **Génération de justification** : Explication médicale (RAG + LLM ou règles)
3. **Construction du résultat** : `TriageResult` complet avec métriques

### `TriageTools`

Outils utilisés par l'agent :
- Chargement et appel du modèle ML
- Initialisation et utilisation du RAG Engine
- Justifications fallback basées sur règles

## Utilisation

### CLI - Script `run_triage.py`

```bash
# Patient aléatoire
python scripts/run_triage.py --patient-id random

# Patient aléatoire avec détails
python scripts/run_triage.py --patient-id random --verbose

# Patient avec constantes spécifiques
python scripts/run_triage.py \
  --age 70 \
  --fc 125 \
  --spo2 88 \
  --temp 39.2 \
  --motif "Difficulté respiratoire"

# Sans RAG (justifications basées sur règles)
python scripts/run_triage.py --patient-id random --no-rag
```

### Programmatique

```python
from src.agents import TriageAgent
from src.models import Patient, ConstantesVitales

# Initialisation de l'agent
agent = TriageAgent(
    ml_model_path="models/trained/triage_model.json",
    ml_preprocessor_path="models/trained/preprocessor.pkl",
    vector_store_path="data/vector_store/medical_kb",
    use_rag=True,
)

# Création d'un patient
constantes = ConstantesVitales(
    frequence_cardiaque=125,
    pression_systolique=160,
    pression_diastolique=95,
    frequence_respiratoire=28,
    temperature=39.2,
    saturation_oxygene=88,
    echelle_douleur=7,
)

patient = Patient(
    age=70,
    sexe="F",
    motif_consultation="Difficulté respiratoire",
    constantes=constantes,
)

# Triage
result = agent.triage(patient, verbose=True)

# Accès aux résultats
print(f"Niveau : {result.gravity_level.value}")
print(f"Confiance : {result.confidence_score:.0%}")
print(f"Justification : {result.justification}")
print(f"Latence totale : {result.total_latency * 1000:.0f}ms")
```

### Batch de patients

```python
from src.data import PatientGenerator

# Génération de patients
generator = PatientGenerator(seed=42)
patients = generator.generate_dataset(n_samples=10)

# Triage en batch
results = agent.batch_triage(patients, verbose=False)

# Analyse des résultats
for result in results:
    print(f"{result.patient.id[:8]}... → {result.gravity_level.value}")
```

## Flux de Triage

```
┌─────────────┐
│   Patient   │
└──────┬──────┘
       │
       v
┌─────────────┐
│  Agent de   │
│   Triage    │
└──────┬──────┘
       │
       ├─────> [1] Prédiction ML (XGBoost)
       │            - Niveau de gravité
       │            - Score de confiance
       │            - Probabilités par classe
       │
       ├─────> [2] Génération de justification
       │            - RAG : Recherche contexte médical
       │            - LLM : Génération texte
       │            - Fallback : Justification basée sur règles
       │
       v
┌──────────────┐
│ TriageResult │
│              │
│ - Niveau     │
│ - Confiance  │
│ - Justif.    │
│ - Métriques  │
└──────────────┘
```

## Métriques de Performance

L'agent mesure automatiquement :
- **Latence ML** : Temps de prédiction du modèle XGBoost (~1-3ms)
- **Latence LLM** : Temps de génération de justification (~100-500ms avec LLM local)
- **Latence totale** : Somme des deux
- **Score de confiance** : Probabilité de la classe prédite (0-1)

## Modes de Fonctionnement

### Mode RAG (Recommandé)
- Utilise le vector store pour récupérer du contexte médical
- Génère des justifications avec le LLM
- Plus riche et contextualisé

```python
agent = TriageAgent(..., use_rag=True)
```

### Mode Fallback (Sans RAG)
- Justifications basées sur des règles simples
- Analyse des anomalies des constantes vitales
- Plus rapide, pas de dépendance LLM

```python
agent = TriageAgent(..., use_rag=False)
```

## Exemples de Résultats

### Cas ROUGE (Urgence vitale)
```
Patient : 75 ans, M
Motif   : Douleur thoracique intense
FC=145 bpm, PA=85/50 mmHg, SpO2=82%

→ Niveau : ROUGE (100% confiance)
→ Justification : "Patient en urgence vitale présentant hypoxémie sévère
   (SpO2 82%), tachycardie (145 bpm) nécessitant une prise en charge immédiate."
```

### Cas JAUNE (Urgent)
```
Patient : 55 ans, F
Motif   : Fièvre élevée
FC=110 bpm, T=39.5°C, Douleur=6/10

→ Niveau : JAUNE (85% confiance)
→ Justification : "Patient nécessitant une prise en charge rapide en raison
   de fièvre élevée (39.5°C), tachycardie (110 bpm) associé à Fièvre élevée."
```

### Cas GRIS (Non urgent)
```
Patient : 25 ans, M
Motif   : Consultation de suivi
FC=72 bpm, PA=120/80 mmHg, SpO2=99%

→ Niveau : GRIS (98% confiance)
→ Justification : "Patient stable sans signe de détresse présentant
   Consultation de suivi, prise en charge différée possible."
```

## Dépendances

- `src.ml` : Modèle de classification XGBoost
- `src.llm` : Système RAG + LLM
- `src.models` : Structures de données (Patient, TriageResult)
- `src.data` : Génération de patients (pour tests)
