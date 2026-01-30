"""
Implémentation de la Grille FRENCH (FRench Emergency Nurses Classification in-Hospital)
Source: SFMU - FRENCH Triage - V1 Mars 2018

Cette grille définit 6 niveaux de triage (Tri 1 à Tri 5, avec Tri 3A et 3B)
basés sur le motif de recours et les constantes vitales.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple
import re


class FrenchTriageLevel(str, Enum):
    """Niveaux de triage FRENCH"""
    TRI_1 = "Tri 1"   # Détresse vitale majeure - Sans délai
    TRI_2 = "Tri 2"   # Atteinte patente - < 20 min
    TRI_3A = "Tri 3A" # Atteinte potentielle avec comorbidités - < 60 min
    TRI_3B = "Tri 3B" # Atteinte potentielle sans comorbidités - < 90 min
    TRI_4 = "Tri 4"   # Atteinte fonctionnelle stable - < 120 min
    TRI_5 = "Tri 5"   # Pas d'atteinte évidente - < 240 min


class GravityLevel(str, Enum):
    """Mapping FRENCH vers 4 niveaux simplifiés"""
    ROUGE = "ROUGE"  # Tri 1, Tri 2
    JAUNE = "JAUNE"  # Tri 3A, Tri 3B
    VERT = "VERT"    # Tri 4
    GRIS = "GRIS"    # Tri 5


# Mapping FRENCH -> 4 niveaux
FRENCH_TO_GRAVITY = {
    FrenchTriageLevel.TRI_1: GravityLevel.ROUGE,
    FrenchTriageLevel.TRI_2: GravityLevel.ROUGE,
    FrenchTriageLevel.TRI_3A: GravityLevel.JAUNE,
    FrenchTriageLevel.TRI_3B: GravityLevel.JAUNE,
    FrenchTriageLevel.TRI_4: GravityLevel.VERT,
    FrenchTriageLevel.TRI_5: GravityLevel.GRIS,
}

# Délais de prise en charge par niveau
DELAI_PRISE_EN_CHARGE = {
    FrenchTriageLevel.TRI_1: "Sans délai (IDE et Médecin)",
    FrenchTriageLevel.TRI_2: "Infirmière < 10 min, Médecin < 20 min",
    FrenchTriageLevel.TRI_3A: "Médecin < 60 min",
    FrenchTriageLevel.TRI_3B: "Médecin < 90 min",
    FrenchTriageLevel.TRI_4: "Médecin < 120 min",
    FrenchTriageLevel.TRI_5: "Médecin < 240 min",
}

# Orientation par niveau
ORIENTATION = {
    FrenchTriageLevel.TRI_1: "SAUV (Salle d'Accueil des Urgences Vitales)",
    FrenchTriageLevel.TRI_2: "SAUV ou Box",
    FrenchTriageLevel.TRI_3A: "Box ou SAUV",
    FrenchTriageLevel.TRI_3B: "Box ou salle d'attente",
    FrenchTriageLevel.TRI_4: "Box ou salle d'attente",
    FrenchTriageLevel.TRI_5: "Box, salle d'attente ou maison médicale de garde",
}


@dataclass
class ConstantesVitales:
    """Constantes vitales pour l'évaluation FRENCH"""
    frequence_cardiaque: int      # FC en bpm
    frequence_respiratoire: int   # FR en cycles/min
    saturation_oxygene: float     # SpO2 en %
    pression_systolique: int      # PAS en mmHg
    pression_diastolique: int     # PAD en mmHg
    temperature: float            # T° en °C
    echelle_douleur: int          # EVA 0-10
    glasgow: Optional[int] = 15   # GCS (défaut: 15 = normal)


class FrenchTriageEngine:
    """
    Moteur de triage basé sur la grille FRENCH

    Implémente les règles officielles de la SFMU pour le triage
    des patients aux urgences.
    """

    def __init__(self):
        # Mots-clés par catégorie de motif
        self.motif_keywords = self._init_motif_keywords()

    def _init_motif_keywords(self) -> dict:
        """Initialise les mots-clés pour la détection des motifs"""
        return {
            # CARDIO-CIRCULATOIRE
            "arret_cardiaque": ["arrêt cardiaque", "acr", "arrêt cardio", "pas de pouls", "réanimation"],
            "hypotension": ["hypotension", "collapsus", "choc", "malaise", "syncope"],
            "douleur_thoracique": ["douleur thoracique", "douleur poitrine", "oppression", "infarctus", "sca", "syndrome coronaire"],
            "tachycardie": ["tachycardie", "palpitations", "cœur rapide"],
            "bradycardie": ["bradycardie", "cœur lent", "pouls lent"],
            "dyspnee_cardiaque": ["dyspnée", "essoufflement", "insuffisance cardiaque", "œdème pulmonaire"],
            "hta": ["hypertension", "tension élevée", "hta"],

            # NEUROLOGIE
            "coma": ["coma", "inconscient", "non réactif", "altération conscience"],
            "avc": ["avc", "paralysie", "hémiplégie", "aphasie", "déficit moteur", "déficit sensitif"],
            "convulsions": ["convulsion", "crise épilepsie", "épilepsie", "crise comitiale"],
            "cephalee": ["céphalée", "mal de tête", "migraine"],
            "confusion": ["confusion", "désorientation", "désorienté"],
            "vertiges": ["vertige", "étourdissement", "trouble équilibre"],

            # RESPIRATOIRE
            "detresse_respi": ["détresse respiratoire", "dyspnée sévère", "asphyxie", "tirage"],
            "asthme": ["asthme", "crise asthme", "bronchospasme", "sifflement"],
            "hemoptysie": ["hémoptysie", "crache sang", "sang toux"],
            "pneumothorax": ["pneumothorax", "embolie pulmonaire"],

            # TRAUMATOLOGIE
            "amputation": ["amputation", "membre sectionné", "doigt coupé"],
            "trauma_cranien": ["traumatisme crânien", "tc", "choc tête", "perte connaissance"],
            "trauma_thorax": ["traumatisme thorax", "trauma thoracique", "accident"],
            "fracture": ["fracture", "os cassé", "déformation"],
            "plaie": ["plaie", "coupure", "lacération", "saignement"],
            "brulure": ["brûlure", "brulure"],

            # ABDOMINAL
            "hematemese": ["hématémèse", "vomissement sang"],
            "rectorragie": ["rectorragie", "sang selles", "méléna"],
            "douleur_abdo": ["douleur abdominale", "mal ventre", "douleur ventre"],
            "occlusion": ["occlusion", "vomissements", "arrêt matières"],

            # PSYCHIATRIE
            "suicidaire": ["suicidaire", "suicide", "tentative suicide", "idées noires"],
            "agitation": ["agitation", "violence", "agressif", "délire"],
            "anxiete": ["anxiété", "angoisse", "attaque panique", "crise angoisse"],

            # DIVERS
            "intoxication": ["intoxication", "overdose", "empoisonnement", "surdosage"],
            "hypoglycemie": ["hypoglycémie", "malaise diabète"],
            "hyperglycemie": ["hyperglycémie", "diabète décompensé", "cétose"],
            "fievre": ["fièvre", "température élevée", "hyperthermie"],
            "hypothermie": ["hypothermie", "froid"],
        }

    def evaluate_constantes(self, constantes: ConstantesVitales, age: int) -> Tuple[FrenchTriageLevel, List[str]]:
        """
        Évalue les constantes vitales selon les seuils FRENCH

        Retourne le niveau de triage basé sur les constantes et les alertes.
        """
        alerts = []
        max_level = FrenchTriageLevel.TRI_5

        # === PAS (Pression Artérielle Systolique) ===
        if constantes.pression_systolique < 70:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_1)
            alerts.append(f"Hypotension sévère: PAS {constantes.pression_systolique} mmHg < 70")
        elif constantes.pression_systolique <= 90 or (constantes.pression_systolique <= 100 and constantes.frequence_cardiaque > 100):
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Hypotension: PAS {constantes.pression_systolique} mmHg")

        # === Fréquence Cardiaque ===
        if constantes.frequence_cardiaque > 180 or constantes.frequence_cardiaque < 40:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_1)
            alerts.append(f"FC critique: {constantes.frequence_cardiaque} bpm")
        elif 130 <= constantes.frequence_cardiaque <= 180:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Tachycardie: FC {constantes.frequence_cardiaque} bpm")
        elif 40 <= constantes.frequence_cardiaque <= 50:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_3B)
            alerts.append(f"Bradycardie: FC {constantes.frequence_cardiaque} bpm")

        # === Saturation O2 ===
        if constantes.saturation_oxygene < 86:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_1)
            alerts.append(f"Hypoxie sévère: SpO2 {constantes.saturation_oxygene}%")
        elif 86 <= constantes.saturation_oxygene <= 90:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Hypoxie: SpO2 {constantes.saturation_oxygene}%")

        # === Fréquence Respiratoire ===
        if constantes.frequence_respiratoire > 40:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_1)
            alerts.append(f"Détresse respiratoire: FR {constantes.frequence_respiratoire}/min")
        elif 30 <= constantes.frequence_respiratoire <= 40:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Polypnée: FR {constantes.frequence_respiratoire}/min")

        # === Glasgow (GCS) ===
        if constantes.glasgow and constantes.glasgow <= 8:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_1)
            alerts.append(f"Coma: GCS {constantes.glasgow}")
        elif constantes.glasgow and 9 <= constantes.glasgow <= 13:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Altération conscience: GCS {constantes.glasgow}")

        # === Température ===
        if constantes.temperature >= 40 or constantes.temperature <= 32:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Température critique: {constantes.temperature}°C")
        elif constantes.temperature <= 35.2:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_2)
            alerts.append(f"Hypothermie: {constantes.temperature}°C")

        # === Douleur ===
        if constantes.echelle_douleur >= 8:
            max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_3B)
            alerts.append(f"Douleur intense: EVA {constantes.echelle_douleur}/10")

        # === Ajustements pédiatriques ===
        if age <= 2:
            # Seuils différents pour les nourrissons
            if age < 1 and constantes.frequence_cardiaque >= 180:
                max_level = self._upgrade_level(max_level, FrenchTriageLevel.TRI_3A)
                alerts.append(f"Tachycardie nourrisson: FC {constantes.frequence_cardiaque} bpm")

        return max_level, alerts

    def evaluate_motif(self, motif: str) -> Tuple[FrenchTriageLevel, str, List[str]]:
        """
        Évalue le motif de consultation selon la grille FRENCH

        Retourne le niveau de triage, la catégorie et les recommandations.
        """
        motif_lower = motif.lower()
        recommendations = []

        # === TRI 1 - Détresse vitale majeure ===
        if self._match_keywords(motif_lower, self.motif_keywords["arret_cardiaque"]):
            return FrenchTriageLevel.TRI_1, "CARDIO-CIRCULATOIRE", ["Réanimation immédiate", "Appel réanimateur"]

        if self._match_keywords(motif_lower, self.motif_keywords["amputation"]):
            return FrenchTriageLevel.TRI_1, "TRAUMATOLOGIE", ["Conservation du membre", "Hémostase"]

        # === TRI 2 ===
        if self._match_keywords(motif_lower, self.motif_keywords["coma"]):
            return FrenchTriageLevel.TRI_2, "NEUROLOGIE", ["Protection voies aériennes", "Glycémie capillaire"]

        if self._match_keywords(motif_lower, self.motif_keywords["avc"]):
            recommendations = ["Alerte thrombolyse", "Heure début symptômes", "Glycémie"]
            return FrenchTriageLevel.TRI_2, "NEUROLOGIE", recommendations

        if self._match_keywords(motif_lower, self.motif_keywords["suicidaire"]):
            return FrenchTriageLevel.TRI_2, "PSYCHIATRIE", ["Surveillance rapprochée", "Retrait objets dangereux"]

        if self._match_keywords(motif_lower, self.motif_keywords["hematemese"]):
            return FrenchTriageLevel.TRI_2, "ABDOMINAL", ["2 VVP gros calibre", "Groupe sanguin RAI"]

        # === TRI 3A/3B ===
        if self._match_keywords(motif_lower, self.motif_keywords["douleur_thoracique"]):
            recommendations = ["ECG immédiat", "Monitoring", "Voie veineuse"]
            return FrenchTriageLevel.TRI_3B, "CARDIO-CIRCULATOIRE", recommendations

        if self._match_keywords(motif_lower, self.motif_keywords["convulsions"]):
            return FrenchTriageLevel.TRI_3B, "NEUROLOGIE", ["Position latérale sécurité", "Protection"]

        if self._match_keywords(motif_lower, self.motif_keywords["asthme"]):
            recommendations = ["Mesure DEP", "Nébulisation", "SpO2"]
            return FrenchTriageLevel.TRI_3B, "RESPIRATOIRE", recommendations

        if self._match_keywords(motif_lower, self.motif_keywords["douleur_abdo"]):
            return FrenchTriageLevel.TRI_3B, "ABDOMINAL", ["Évaluation chirurgicale si défense"]

        if self._match_keywords(motif_lower, self.motif_keywords["intoxication"]):
            return FrenchTriageLevel.TRI_3B, "INTOXICATION", ["Identification toxique", "Appel centre antipoison"]

        # === TRI 4 ===
        if self._match_keywords(motif_lower, self.motif_keywords["fracture"]):
            return FrenchTriageLevel.TRI_4, "TRAUMATOLOGIE", ["Immobilisation", "Antalgie", "Radio"]

        if self._match_keywords(motif_lower, self.motif_keywords["plaie"]):
            return FrenchTriageLevel.TRI_4, "TRAUMATOLOGIE", ["Hémostase", "Désinfection", "VAT"]

        if self._match_keywords(motif_lower, self.motif_keywords["anxiete"]):
            return FrenchTriageLevel.TRI_4, "PSYCHIATRIE", ["Environnement calme", "Réassurance"]

        # === TRI 5 ===
        if self._match_keywords(motif_lower, self.motif_keywords["fievre"]):
            return FrenchTriageLevel.TRI_5, "INFECTIOLOGIE", ["Paracétamol si besoin"]

        if self._match_keywords(motif_lower, self.motif_keywords["cephalee"]):
            # Céphalée sans signe de gravité
            return FrenchTriageLevel.TRI_5, "NEUROLOGIE", ["Antalgie simple"]

        # Par défaut: Tri 4 (consultation non urgente mais justifiée)
        return FrenchTriageLevel.TRI_4, "DIVERS", ["Évaluation médicale standard"]

    def triage(
        self,
        age: int,
        sexe: str,
        motif: str,
        constantes: ConstantesVitales,
        antecedents: Optional[List[str]] = None
    ) -> dict:
        """
        Effectue le triage complet d'un patient

        Combine l'évaluation des constantes et du motif pour déterminer
        le niveau de triage final.
        """
        # Évaluer les constantes
        constantes_level, constantes_alerts = self.evaluate_constantes(constantes, age)

        # Évaluer le motif
        motif_level, categorie, recommendations = self.evaluate_motif(motif)

        # Le niveau final est le plus grave entre constantes et motif
        final_level = self._upgrade_level(motif_level, constantes_level)

        # Ajuster si comorbidités (3B -> 3A)
        if final_level == FrenchTriageLevel.TRI_3B and antecedents and len(antecedents) > 0:
            comorbidites_lourdes = ["diabète", "insuffisance cardiaque", "insuffisance rénale",
                                    "cancer", "immunodépression", "dialyse"]
            if any(c.lower() in " ".join(antecedents).lower() for c in comorbidites_lourdes):
                final_level = FrenchTriageLevel.TRI_3A

        # Mapper vers les 4 niveaux
        gravity_level = FRENCH_TO_GRAVITY[final_level]

        return {
            "french_triage_level": final_level.value,
            "gravity_level": gravity_level.value,
            "categorie": categorie,
            "delai_prise_en_charge": DELAI_PRISE_EN_CHARGE[final_level],
            "orientation": ORIENTATION[final_level],
            "red_flags": constantes_alerts,
            "recommendations": recommendations,
            "constantes_level": constantes_level.value,
            "motif_level": motif_level.value
        }

    def _match_keywords(self, text: str, keywords: List[str]) -> bool:
        """Vérifie si le texte contient un des mots-clés"""
        return any(kw in text for kw in keywords)

    def _upgrade_level(self, current: FrenchTriageLevel, new: FrenchTriageLevel) -> FrenchTriageLevel:
        """Retourne le niveau le plus grave entre deux niveaux"""
        priority = {
            FrenchTriageLevel.TRI_1: 1,
            FrenchTriageLevel.TRI_2: 2,
            FrenchTriageLevel.TRI_3A: 3,
            FrenchTriageLevel.TRI_3B: 4,
            FrenchTriageLevel.TRI_4: 5,
            FrenchTriageLevel.TRI_5: 6,
        }
        return current if priority[current] < priority[new] else new
