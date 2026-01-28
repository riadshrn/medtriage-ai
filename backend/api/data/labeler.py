"""
Attribution automatique des niveaux de gravité basée sur des règles médicales.
"""

from src.models import Patient, ConstantesVitales, GravityLevel


class GravityLabeler:
    """
    Attribue automatiquement un niveau de gravité à un patient.

    Utilise des règles médicales simplifiées basées sur :
    - Constantes vitales critiques
    - Âge du patient
    - Motif de consultation
    """

    # Mots-clés critiques dans les motifs
    KEYWORDS_ROUGE = [
        "perte de conscience",
        "hémorragie",
        "avc",
        "choc",
        "détresse respiratoire sévère",
        "traumatisme grave",
        "arrêt",
        "infarctus",
    ]

    KEYWORDS_JAUNE = [
        "douleur thoracique",
        "difficulté respiratoire",
        "fièvre élevée",
        "traumatisme crânien",
        "déshydratation sévère",
        "douleur abdominale intense",
    ]

    KEYWORDS_VERT = [
        "entorse",
        "fièvre modérée",
        "mal de tête",
        "nausées",
        "douleur dorsale",
        "douleur abdominale modérée",
    ]

    @staticmethod
    def label_patient(patient: Patient) -> GravityLevel:
        """
        Attribue un niveau de gravité à un patient.

        Args:
            patient: Patient à évaluer

        Returns:
            GravityLevel: Niveau de gravité attribué
        """
        c = patient.constantes
        age = patient.age
        motif = patient.motif_consultation.lower()

        # Règle 1 : Constantes vitales critiques → ROUGE
        if GravityLabeler._is_critical_vitals(c, age):
            return GravityLevel.ROUGE

        # Règle 2 : Mots-clés du motif → ROUGE
        if any(keyword in motif for keyword in GravityLabeler.KEYWORDS_ROUGE):
            return GravityLevel.ROUGE

        # Règle 3 : Constantes anormales + âge critique → ROUGE
        if (age < 2 or age > 80) and GravityLabeler._is_abnormal_vitals(c):
            return GravityLevel.ROUGE

        # Règle 4 : Constantes anormales significatives → JAUNE
        if GravityLabeler._is_abnormal_vitals(c):
            return GravityLevel.JAUNE

        # Règle 5 : Mots-clés du motif → JAUNE
        if any(keyword in motif for keyword in GravityLabeler.KEYWORDS_JAUNE):
            return GravityLevel.JAUNE

        # Règle 6 : Douleur élevée → JAUNE
        if c.echelle_douleur >= 7:
            return GravityLevel.JAUNE

        # Règle 7 : Mots-clés du motif → VERT
        if any(keyword in motif for keyword in GravityLabeler.KEYWORDS_VERT):
            return GravityLevel.VERT

        # Règle 8 : Constantes légèrement anormales → VERT
        if GravityLabeler._is_slightly_abnormal_vitals(c):
            return GravityLevel.VERT

        # Par défaut → GRIS (non urgent)
        return GravityLevel.GRIS

    @staticmethod
    def _is_critical_vitals(c: ConstantesVitales, age: int) -> bool:
        """
        Vérifie si les constantes sont dans une zone critique.

        Returns:
            bool: True si constantes critiques
        """
        # Fréquence cardiaque critique
        if c.frequence_cardiaque < 40 or c.frequence_cardiaque > 140:
            return True

        # Pression artérielle critique
        if c.pression_systolique < 90 or c.pression_systolique > 200:
            return True

        # Saturation en oxygène critique
        if c.saturation_oxygene < 90:
            return True

        # Fréquence respiratoire critique
        if age > 12:
            if c.frequence_respiratoire < 8 or c.frequence_respiratoire > 30:
                return True
        else:
            if c.frequence_respiratoire < 15 or c.frequence_respiratoire > 40:
                return True

        # Température critique
        if c.temperature < 35.5 or c.temperature > 40.0:
            return True

        # Glycémie critique
        if c.glycemie is not None:
            if c.glycemie < 0.5 or c.glycemie > 4.0:
                return True

        return False

    @staticmethod
    def _is_abnormal_vitals(c: ConstantesVitales) -> bool:
        """
        Vérifie si les constantes sont anormales (mais pas critiques).

        Returns:
            bool: True si constantes anormales
        """
        # Fréquence cardiaque anormale
        if c.frequence_cardiaque < 50 or c.frequence_cardiaque > 110:
            return True

        # Pression artérielle anormale
        if c.pression_systolique < 100 or c.pression_systolique > 160:
            return True

        # Saturation en oxygène anormale
        if c.saturation_oxygene < 94:
            return True

        # Fréquence respiratoire anormale
        if c.frequence_respiratoire < 10 or c.frequence_respiratoire > 25:
            return True

        # Température anormale
        if c.temperature < 36.0 or c.temperature > 38.5:
            return True

        return False

    @staticmethod
    def _is_slightly_abnormal_vitals(c: ConstantesVitales) -> bool:
        """
        Vérifie si les constantes sont légèrement anormales.

        Returns:
            bool: True si constantes légèrement anormales
        """
        # Fièvre modérée
        if 37.5 < c.temperature < 38.5:
            return True

        # Douleur modérée
        if 3 <= c.echelle_douleur < 7:
            return True

        # Tachycardie légère
        if 100 < c.frequence_cardiaque < 110:
            return True

        return False
