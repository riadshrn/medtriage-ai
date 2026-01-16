"""
Niveaux de gravité pour le triage des patients aux urgences.

Basé sur le système de classification français (similaire au système ESI).
"""

from enum import Enum


class GravityLevel(str, Enum):
    """
    Niveaux de gravité du triage.

    - GRIS : Non urgent - Patient stable, peut attendre plusieurs heures
    - VERT : Peu urgent - Problème mineur, attente acceptable
    - JAUNE : Urgent - Nécessite une prise en charge rapide
    - ROUGE : Très urgent - Urgence vitale, prise en charge immédiate
    """

    GRIS = "GRIS"
    VERT = "VERT"
    JAUNE = "JAUNE"
    ROUGE = "ROUGE"

    @property
    def priority(self) -> int:
        """
        Retourne le niveau de priorité (1 = le plus urgent).

        Returns:
            int: Niveau de priorité (1-4)
        """
        priority_map = {
            GravityLevel.ROUGE: 1,
            GravityLevel.JAUNE: 2,
            GravityLevel.VERT: 3,
            GravityLevel.GRIS: 4,
        }
        return priority_map[self]

    @property
    def description(self) -> str:
        """
        Retourne une description textuelle du niveau.

        Returns:
            str: Description du niveau de gravité
        """
        descriptions = {
            GravityLevel.ROUGE: "Urgence vitale - Prise en charge immédiate",
            GravityLevel.JAUNE: "Urgent - Prise en charge rapide nécessaire",
            GravityLevel.VERT: "Peu urgent - Attente acceptable",
            GravityLevel.GRIS: "Non urgent - Peut attendre plusieurs heures",
        }
        return descriptions[self]

    def __str__(self) -> str:
        return self.value
