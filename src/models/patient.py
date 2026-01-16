"""
Modèle représentant un patient aux urgences.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .constantes_vitales import ConstantesVitales


@dataclass
class Patient:
    """
    Représente un patient aux urgences.

    Attributes:
        id: Identifiant unique du patient
        age: Âge du patient (en années)
        sexe: Sexe du patient ('M', 'F', ou 'Autre')
        motif_consultation: Raison de la venue aux urgences
        constantes: Constantes vitales mesurées
        antecedents: Antécédents médicaux importants (optionnel)
        traitements_en_cours: Traitements médicamenteux actuels (optionnel)
        timestamp: Date et heure d'arrivée
    """

    age: int
    sexe: str
    motif_consultation: str
    constantes: ConstantesVitales
    antecedents: Optional[str] = None
    traitements_en_cours: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validation des données patient."""
        self._validate()

    def _validate(self) -> None:
        """
        Valide les données du patient.

        Raises:
            ValueError: Si une valeur est invalide
        """
        if not 0 <= self.age <= 120:
            raise ValueError(f"Âge invalide: {self.age} ans")

        if self.sexe not in ["M", "F", "Autre"]:
            raise ValueError(f"Sexe invalide: {self.sexe} (doit être 'M', 'F' ou 'Autre')")

        if not self.motif_consultation or len(self.motif_consultation.strip()) == 0:
            raise ValueError("Le motif de consultation ne peut pas être vide")

    def to_dict(self) -> dict:
        """
        Convertit le patient en dictionnaire.

        Returns:
            dict: Représentation dictionnaire du patient
        """
        return {
            "id": self.id,
            "age": self.age,
            "sexe": self.sexe,
            "motif_consultation": self.motif_consultation,
            "constantes": self.constantes.to_dict(),
            "antecedents": self.antecedents,
            "traitements_en_cours": self.traitements_en_cours,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"Patient(id={self.id[:8]}..., age={self.age}, sexe={self.sexe}, "
            f"motif='{self.motif_consultation[:30]}...')"
        )
