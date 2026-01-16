"""
Constantes vitales d'un patient.

Ces valeurs sont utilisées par le modèle ML pour la classification.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConstantesVitales:
    """
    Constantes vitales mesurées lors du triage.

    Attributes:
        frequence_cardiaque: Fréquence cardiaque (bpm - battements par minute)
        pression_systolique: Pression artérielle systolique (mmHg)
        pression_diastolique: Pression artérielle diastolique (mmHg)
        frequence_respiratoire: Fréquence respiratoire (respirations/min)
        temperature: Température corporelle (°C)
        saturation_oxygene: Saturation en oxygène (SpO2 en %)
        echelle_douleur: Échelle de douleur (0-10)
        glycemie: Glycémie capillaire (g/L) - optionnel
    """

    frequence_cardiaque: int
    pression_systolique: int
    pression_diastolique: int
    frequence_respiratoire: int
    temperature: float
    saturation_oxygene: int
    echelle_douleur: int
    glycemie: Optional[float] = None

    def __post_init__(self) -> None:
        """Validation des constantes vitales."""
        self._validate()

    def _validate(self) -> None:
        """
        Valide les valeurs des constantes vitales.

        Raises:
            ValueError: Si une valeur est hors des limites physiologiques
        """
        if not 20 <= self.frequence_cardiaque <= 250:
            raise ValueError(
                f"Fréquence cardiaque invalide: {self.frequence_cardiaque} bpm"
            )

        if not 50 <= self.pression_systolique <= 250:
            raise ValueError(
                f"Pression systolique invalide: {self.pression_systolique} mmHg"
            )

        if not 30 <= self.pression_diastolique <= 150:
            raise ValueError(
                f"Pression diastolique invalide: {self.pression_diastolique} mmHg"
            )

        if not 5 <= self.frequence_respiratoire <= 60:
            raise ValueError(
                f"Fréquence respiratoire invalide: {self.frequence_respiratoire} /min"
            )

        if not 32.0 <= self.temperature <= 43.0:
            raise ValueError(f"Température invalide: {self.temperature}°C")

        if not 50 <= self.saturation_oxygene <= 100:
            raise ValueError(
                f"Saturation en oxygène invalide: {self.saturation_oxygene}%"
            )

        if not 0 <= self.echelle_douleur <= 10:
            raise ValueError(
                f"Échelle de douleur invalide: {self.echelle_douleur} (doit être 0-10)"
            )

        if self.glycemie is not None and not 0.2 <= self.glycemie <= 6.0:
            raise ValueError(f"Glycémie invalide: {self.glycemie} g/L")

    def to_dict(self) -> dict:
        """
        Convertit les constantes en dictionnaire (pour ML).

        Returns:
            dict: Dictionnaire des constantes vitales
        """
        return {
            "frequence_cardiaque": self.frequence_cardiaque,
            "pression_systolique": self.pression_systolique,
            "pression_diastolique": self.pression_diastolique,
            "frequence_respiratoire": self.frequence_respiratoire,
            "temperature": self.temperature,
            "saturation_oxygene": self.saturation_oxygene,
            "echelle_douleur": self.echelle_douleur,
            "glycemie": self.glycemie or 1.0,  # Valeur par défaut si non mesurée
        }
