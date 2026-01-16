"""
Résultat du triage d'un patient.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .gravity_level import GravityLevel
from .patient import Patient


@dataclass
class TriageResult:
    """
    Résultat du triage d'un patient.

    Attributes:
        patient: Patient évalué
        gravity_level: Niveau de gravité assigné
        justification: Explication médicale du niveau de gravité (générée par LLM)
        confidence_score: Score de confiance du modèle ML (0-1)
        ml_probabilities: Probabilités pour chaque classe (optionnel)
        latency_ml: Temps de calcul du modèle ML (en secondes)
        latency_llm: Temps de génération de la justification (en secondes)
        timestamp: Date et heure du triage
    """

    patient: Patient
    gravity_level: GravityLevel
    justification: str
    confidence_score: float
    ml_probabilities: Optional[dict[str, float]] = None
    latency_ml: Optional[float] = None
    latency_llm: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validation du résultat de triage."""
        self._validate()

    def _validate(self) -> None:
        """
        Valide les données du résultat de triage.

        Raises:
            ValueError: Si une valeur est invalide
        """
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                f"Score de confiance invalide: {self.confidence_score} (doit être entre 0 et 1)"
            )

        if not self.justification or len(self.justification.strip()) == 0:
            raise ValueError("La justification ne peut pas être vide")

        if self.latency_ml is not None and self.latency_ml < 0:
            raise ValueError(f"Latence ML invalide: {self.latency_ml}s")

        if self.latency_llm is not None and self.latency_llm < 0:
            raise ValueError(f"Latence LLM invalide: {self.latency_llm}s")

    @property
    def total_latency(self) -> Optional[float]:
        """
        Calcule la latence totale (ML + LLM).

        Returns:
            Optional[float]: Latence totale en secondes, ou None si indisponible
        """
        if self.latency_ml is not None and self.latency_llm is not None:
            return self.latency_ml + self.latency_llm
        return None

    def to_dict(self) -> dict:
        """
        Convertit le résultat en dictionnaire.

        Returns:
            dict: Représentation dictionnaire du résultat
        """
        return {
            "patient": self.patient.to_dict(),
            "gravity_level": self.gravity_level.value,
            "justification": self.justification,
            "confidence_score": self.confidence_score,
            "ml_probabilities": self.ml_probabilities,
            "latency_ml": self.latency_ml,
            "latency_llm": self.latency_llm,
            "total_latency": self.total_latency,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"TriageResult(patient={self.patient.id[:8]}..., "
            f"level={self.gravity_level.value}, confidence={self.confidence_score:.2f})"
        )
