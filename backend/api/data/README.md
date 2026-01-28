# Module de Génération de Données Synthétiques

Ce module permet de générer des patients synthétiques réalistes pour l'entraînement du modèle de triage.

## Composants

### `PatientGenerator`

Génère des patients synthétiques avec des constantes vitales réalistes selon des distributions physiologiques.

**Caractéristiques** :
- Génération basée sur des profils de gravité (GRIS/VERT/JAUNE/ROUGE)
- Distributions réalistes des constantes vitales
- Prise en compte de l'âge dans les paramètres physiologiques
- Motifs de consultation contextualisés
- Antécédents médicaux et traitements

### `GravityLabeler`

Attribue automatiquement un niveau de gravité aux patients générés basé sur des règles médicales simplifiées.

**Règles de classification** :
1. Constantes vitales critiques → ROUGE
2. Mots-clés critiques (hémorragie, AVC, etc.) → ROUGE
3. Constantes anormales + âge extrême → ROUGE
4. Constantes anormales → JAUNE
5. Douleur élevée (≥7/10) → JAUNE
6. Constantes légèrement anormales → VERT
7. Par défaut → GRIS

## Utilisation

### Génération d'un dataset complet

```bash
python scripts/generate_dataset.py --n_samples 1000 --output data/raw/patients_synthetic.csv
```

### Génération programmatique

```python
from src.data import PatientGenerator, GravityLabeler

# Génération de patients
generator = PatientGenerator(seed=42)
patients = generator.generate_dataset(n_samples=1000)

# Attribution des niveaux de gravité
labeler = GravityLabeler()
for patient in patients:
    gravity = labeler.label_patient(patient)
    print(f"{patient.id}: {gravity.value}")
```

## Distribution par défaut

Le dataset généré suit une distribution réaliste des urgences :

- **GRIS** : ~20% (non urgent)
- **VERT** : ~50% (peu urgent)
- **JAUNE** : ~25% (urgent)
- **ROUGE** : ~5% (très urgent)

## Format du dataset

Le fichier CSV généré contient les colonnes suivantes :

| Colonne | Description |
|---------|-------------|
| `id` | Identifiant unique du patient (UUID) |
| `age` | Âge en années |
| `sexe` | M, F, ou Autre |
| `motif_consultation` | Raison de la venue aux urgences |
| `frequence_cardiaque` | Fréquence cardiaque (bpm) |
| `pression_systolique` | Pression systolique (mmHg) |
| `pression_diastolique` | Pression diastolique (mmHg) |
| `frequence_respiratoire` | Fréquence respiratoire (/min) |
| `temperature` | Température corporelle (°C) |
| `saturation_oxygene` | SpO2 (%) |
| `echelle_douleur` | Échelle de douleur (0-10) |
| `glycemie` | Glycémie capillaire (g/L) - optionnel |
| `antecedents` | Antécédents médicaux - optionnel |
| `traitements_en_cours` | Traitements actuels - optionnel |
| `gravity_level` | Niveau de gravité (GRIS/VERT/JAUNE/ROUGE) |

## Tests

```bash
# Lancer les tests de generation de donnees
python -m pytest tests/test_data_generation.py -v
```

### Resultats des tests

| Test | Description | Statut |
|------|-------------|--------|
| test_generate_single_patient | Generation d'un patient | PASSED |
| test_generate_patient_with_target_gravity | Generation avec gravite cible | PASSED |
| test_generate_dataset | Generation d'un dataset | PASSED |
| test_generate_dataset_with_custom_distribution | Distribution personnalisee | PASSED |
| test_seed_consistency | Reproductibilite avec seed | PASSED |
| test_label_critical_patient | Labellisation patient critique | PASSED |
| test_label_stable_patient | Labellisation patient stable | PASSED |
| test_label_moderate_urgency | Labellisation urgence moderee | PASSED |
| test_label_with_keywords | Detection des mots-cles | PASSED |
| test_label_elderly_with_abnormal_vitals | Patient age avec anomalies | PASSED |

**Total : 10 tests - 10 passed**
