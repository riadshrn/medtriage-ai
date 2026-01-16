"""
Modèles de données pour RedFlag-AI.

Ce module contient les structures de données principales :
- GravityLevel : Niveaux de gravité du triage
- ConstantesVitales : Constantes vitales du patient
- Patient : Informations patient
- TriageResult : Résultat du triage
"""

from .gravity_level import GravityLevel
from .constantes_vitales import ConstantesVitales
from .patient import Patient
from .triage_result import TriageResult

__all__ = [
    "GravityLevel",
    "ConstantesVitales",
    "Patient",
    "TriageResult",
]
