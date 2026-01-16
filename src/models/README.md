# Modeles de donnees

Ce module contient les structures de donnees principales du systeme de triage.

## Classes

### GravityLevel
Enumeration des 4 niveaux de gravite du triage medical :
- **ROUGE** (priorite 1) : Urgence vitale immediate
- **JAUNE** (priorite 2) : Urgence relative
- **VERT** (priorite 3) : Consultation standard
- **GRIS** (priorite 4) : Non urgent

### ConstantesVitales
Constantes vitales du patient avec validation :
- `frequence_cardiaque` : 20-250 bpm
- `pression_arterielle_systolique` : 50-250 mmHg
- `pression_arterielle_diastolique` : 30-150 mmHg
- `temperature` : 30.0-45.0 C
- `saturation_o2` : 50-100 %
- `frequence_respiratoire` : 5-60 /min
- `glycemie` (optionnel) : g/L
- `score_douleur` (optionnel) : 0-10

### Patient
Informations patient avec validation :
- `id` : Identifiant unique
- `age` : 0-120 ans
- `sexe` : "M" ou "F"
- `motif_consultation` : Motif de la consultation
- `constantes` : ConstantesVitales
- `antecedents` : Liste des antecedents medicaux
- `allergies` : Liste des allergies
- `timestamp` : Date/heure d'arrivee

### TriageResult
Resultat du triage avec metriques :
- `patient_id` : ID du patient
- `gravity_level` : Niveau de gravite
- `confidence_score` : Score de confiance (0-1)
- `justification` : Explication medicale
- `ml_latency_ms` : Temps ML en ms
- `llm_latency_ms` : Temps LLM en ms
- `red_flags` : Liste des signaux d'alerte

## Tests

```bash
# Lancer les tests des modeles
python -m pytest tests/test_models.py -v
```

### Resultats des tests

| Test | Description | Statut |
|------|-------------|--------|
| test_priority_order | Ordre de priorite des niveaux | PASSED |
| test_descriptions | Descriptions des niveaux | PASSED |
| test_string_representation | Representation textuelle | PASSED |
| test_valid_constantes | Constantes valides | PASSED |
| test_invalid_frequence_cardiaque | Validation frequence cardiaque | PASSED |
| test_invalid_temperature | Validation temperature | PASSED |
| test_to_dict | Serialisation dictionnaire | PASSED |
| test_valid_patient | Patient valide | PASSED |
| test_invalid_age | Validation age | PASSED |
| test_invalid_sexe | Validation sexe | PASSED |
| test_empty_motif | Validation motif | PASSED |
| test_valid_triage_result | Resultat valide | PASSED |
| test_invalid_confidence_score | Validation score confiance | PASSED |
| test_empty_justification | Validation justification | PASSED |
| test_total_latency | Calcul latence totale | PASSED |

**Total : 17 tests - 17 passed**

## Utilisation

```python
from src.models import Patient, ConstantesVitales, GravityLevel, TriageResult

# Creer des constantes vitales
constantes = ConstantesVitales(
    frequence_cardiaque=85,
    pression_arterielle_systolique=130,
    pression_arterielle_diastolique=85,
    temperature=37.2,
    saturation_o2=98,
    frequence_respiratoire=16,
    score_douleur=3
)

# Creer un patient
patient = Patient(
    id="P001",
    age=45,
    sexe="M",
    motif_consultation="Douleur thoracique",
    constantes=constantes,
    antecedents=["Hypertension"],
    allergies=[]
)

# Creer un resultat de triage
result = TriageResult(
    patient_id="P001",
    gravity_level=GravityLevel.JAUNE,
    confidence_score=0.87,
    justification="Douleur thoracique necessitant evaluation cardiaque",
    ml_latency_ms=15.2,
    llm_latency_ms=234.5,
    red_flags=["Douleur thoracique"]
)
```
