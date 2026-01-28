"""
Configuration canonique des features pour le modele ML de triage.

Ce fichier sert de source unique de verite pour:
- Les features requises vs optionnelles
- Les valeurs par defaut pour l'imputation
- L'evaluation de la qualite des donnees
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional


class PredictionQuality(str, Enum):
    """Niveau de qualite des donnees pour la prediction."""
    HIGH = "high"              # Toutes les features critiques presentes
    MEDIUM = "medium"          # Features critiques ok, certaines importantes manquantes
    LOW = "low"                # Features critiques manquantes
    INSUFFICIENT = "insufficient"  # Impossible de faire une prediction fiable


# =============================================================================
# DEFINITION DES FEATURES
# =============================================================================

# Features absolument necessaires pour une prediction fiable
REQUIRED_FEATURES: List[str] = [
    "age",
    "sexe",
    "frequence_cardiaque",
    "pression_systolique",
    "pression_diastolique",
    "frequence_respiratoire",
    "temperature",
    "saturation_oxygene",
]

# Features importantes mais pouvant etre imputees
IMPORTANT_FEATURES: List[str] = [
    "echelle_douleur",
    "glasgow",
]

# Features optionnelles
OPTIONAL_FEATURES: List[str] = [
    "glycemie",
]

# Toutes les features utilisees par le modele (dans l'ordre)
ALL_ML_FEATURES: List[str] = [
    "age",
    "sexe",
    "frequence_cardiaque",
    "pression_systolique",
    "pression_diastolique",
    "frequence_respiratoire",
    "temperature",
    "saturation_oxygene",
    "echelle_douleur",
    "glycemie",
    "glasgow",
]

# Colonnes a exclure lors du preprocessing (non utilisees par le ML)
COLUMNS_TO_DROP: List[str] = [
    "id",
    "motif_consultation",
    "antecedents",
    "traitements_en_cours",
]


# =============================================================================
# VALEURS PAR DEFAUT POUR L'IMPUTATION
# =============================================================================

DEFAULT_VALUES: Dict[str, float] = {
    # Valeurs "normales" cliniquement acceptables
    "age": 45,                      # Age moyen
    "sexe": 0,                      # M=0 (apres encodage)
    "frequence_cardiaque": 80,      # bpm normal
    "pression_systolique": 120,     # mmHg normal
    "pression_diastolique": 80,     # mmHg normal
    "frequence_respiratoire": 16,   # cycles/min normal
    "temperature": 37.0,            # Celsius normal
    "saturation_oxygene": 98,       # % normal
    "echelle_douleur": 0,           # Pas de douleur
    "glycemie": 1.0,                # g/L normal
    "glasgow": 15,                  # Score max (conscient)
}

# Encodage du sexe
SEXE_ENCODING: Dict[str, int] = {
    "M": 0,
    "F": 1,
    "Autre": 2,
}


# =============================================================================
# PLAGES DE VALIDATION
# =============================================================================

FEATURE_RANGES: Dict[str, Tuple[float, float]] = {
    "age": (0, 120),
    "sexe": (0, 2),  # Apres encodage
    "frequence_cardiaque": (0, 300),
    "pression_systolique": (0, 300),
    "pression_diastolique": (0, 200),
    "frequence_respiratoire": (0, 100),
    "temperature": (20.0, 45.0),
    "saturation_oxygene": (0, 100),
    "echelle_douleur": (0, 10),
    "glycemie": (0.0, 10.0),
    "glasgow": (3, 15),
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_all_features() -> List[str]:
    """Retourne toutes les features utilisees par le modele."""
    return ALL_ML_FEATURES.copy()


def get_required_features() -> List[str]:
    """Retourne les features requises pour une prediction fiable."""
    return REQUIRED_FEATURES.copy()


def assess_prediction_quality(
    features: Dict[str, Optional[float]]
) -> Tuple[PredictionQuality, List[str]]:
    """
    Evalue la qualite des donnees pour la prediction.

    Args:
        features: Dictionnaire des features avec leurs valeurs (None si manquante)

    Returns:
        Tuple (niveau_qualite, liste_features_manquantes_critiques)
    """
    missing_required = [
        f for f in REQUIRED_FEATURES
        if f not in features or features[f] is None
    ]

    missing_important = [
        f for f in IMPORTANT_FEATURES
        if f not in features or features[f] is None
    ]

    # Plus de 2 features requises manquantes = insuffisant
    if len(missing_required) > 2:
        return PredictionQuality.INSUFFICIENT, missing_required

    # 1-2 features requises manquantes = qualite basse
    if len(missing_required) > 0:
        return PredictionQuality.LOW, missing_required

    # Features requises ok, mais importantes manquantes = qualite moyenne
    if len(missing_important) > 1:
        return PredictionQuality.MEDIUM, missing_important

    # Tout est present = qualite haute
    return PredictionQuality.HIGH, []


def validate_feature_value(feature_name: str, value: float) -> bool:
    """
    Valide qu'une valeur est dans la plage acceptable.

    Args:
        feature_name: Nom de la feature
        value: Valeur a valider

    Returns:
        True si valide, False sinon
    """
    if feature_name not in FEATURE_RANGES:
        return True  # Pas de validation definie

    min_val, max_val = FEATURE_RANGES[feature_name]
    return min_val <= value <= max_val


def encode_sexe(sexe: str) -> int:
    """Encode le sexe en valeur numerique."""
    return SEXE_ENCODING.get(sexe, SEXE_ENCODING["Autre"])


def impute_missing_features(
    features: Dict[str, Optional[float]],
    use_defaults: bool = True
) -> Tuple[Dict[str, float], List[str]]:
    """
    Impute les valeurs manquantes avec les valeurs par defaut.

    Args:
        features: Dictionnaire des features (certaines peuvent etre None)
        use_defaults: Si True, utilise les valeurs par defaut; sinon leve une erreur

    Returns:
        Tuple (features_imputees, liste_features_imputees)
    """
    imputed = features.copy()
    imputed_list = []

    for feature in ALL_ML_FEATURES:
        if feature not in imputed or imputed[feature] is None:
            if use_defaults and feature in DEFAULT_VALUES:
                imputed[feature] = DEFAULT_VALUES[feature]
                imputed_list.append(feature)
            elif not use_defaults:
                raise ValueError(f"Feature manquante sans valeur par defaut: {feature}")

    return imputed, imputed_list
