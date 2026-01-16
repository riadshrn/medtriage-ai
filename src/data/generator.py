"""
Générateur de patients synthétiques pour l'entraînement du modèle.
"""

import random
from typing import List

from src.models import Patient, ConstantesVitales


class PatientGenerator:
    """
    Génère des patients synthétiques réalistes pour l'entraînement.

    Les données générées respectent des distributions physiologiques réalistes
    et couvrent différents profils de gravité.
    """

    # Motifs de consultation par gravité
    MOTIFS_GRIS = [
        "Consultation de suivi",
        "Renouvellement d'ordonnance",
        "Certificat médical",
        "Petite plaie superficielle",
        "Rhume léger",
    ]

    MOTIFS_VERT = [
        "Entorse légère",
        "Douleur abdominale modérée",
        "Fièvre modérée",
        "Mal de tête persistant",
        "Nausées",
        "Douleur dorsale",
    ]

    MOTIFS_JAUNE = [
        "Douleur thoracique atypique",
        "Difficulté respiratoire modérée",
        "Fièvre élevée avec frissons",
        "Douleur abdominale intense",
        "Traumatisme crânien léger",
        "Déshydratation sévère",
    ]

    MOTIFS_ROUGE = [
        "Douleur thoracique intense",
        "Détresse respiratoire sévère",
        "Perte de conscience",
        "Hémorragie importante",
        "AVC suspecté",
        "Traumatisme grave",
        "Choc",
    ]

    def __init__(self, seed: int = 42):
        """
        Initialise le générateur.

        Args:
            seed: Graine aléatoire pour la reproductibilité
        """
        random.seed(seed)

    def generate_patient(
        self, target_gravity: str = None
    ) -> Patient:
        """
        Génère un patient synthétique.

        Args:
            target_gravity: Niveau de gravité ciblé (GRIS/VERT/JAUNE/ROUGE)
                          Si None, choisit aléatoirement

        Returns:
            Patient: Patient généré
        """
        if target_gravity is None:
            # Distribution réaliste aux urgences
            target_gravity = random.choices(
                ["GRIS", "VERT", "JAUNE", "ROUGE"],
                weights=[0.2, 0.5, 0.25, 0.05],  # Majorité = VERT
            )[0]

        # Génération des données de base
        age = self._generate_age(target_gravity)
        sexe = random.choice(["M", "F", "Autre"])
        motif = self._generate_motif(target_gravity)
        constantes = self._generate_constantes(target_gravity, age)
        antecedents = self._generate_antecedents(age) if random.random() > 0.3 else None
        traitements = self._generate_traitements() if antecedents else None

        return Patient(
            age=age,
            sexe=sexe,
            motif_consultation=motif,
            constantes=constantes,
            antecedents=antecedents,
            traitements_en_cours=traitements,
        )

    def generate_dataset(
        self, n_samples: int = 1000, distribution: dict = None
    ) -> List[Patient]:
        """
        Génère un dataset complet de patients.

        Args:
            n_samples: Nombre de patients à générer
            distribution: Distribution des niveaux de gravité
                         Ex: {"GRIS": 0.2, "VERT": 0.5, "JAUNE": 0.25, "ROUGE": 0.05}

        Returns:
            List[Patient]: Liste des patients générés
        """
        if distribution is None:
            distribution = {"GRIS": 0.2, "VERT": 0.5, "JAUNE": 0.25, "ROUGE": 0.05}

        patients = []
        for _ in range(n_samples):
            target_gravity = random.choices(
                list(distribution.keys()),
                weights=list(distribution.values()),
            )[0]
            patients.append(self.generate_patient(target_gravity))

        return patients

    def _generate_age(self, gravity: str) -> int:
        """
        Génère un âge réaliste selon la gravité.
        Les patients plus âgés ont tendance à avoir des cas plus graves.
        """
        if gravity == "ROUGE":
            # Cas graves : souvent personnes âgées ou très jeunes
            if random.random() < 0.3:
                return random.randint(0, 5)  # Enfants
            return random.randint(60, 95)  # Seniors

        elif gravity == "JAUNE":
            return random.randint(30, 80)

        elif gravity == "VERT":
            return random.randint(15, 70)

        else:  # GRIS
            return random.randint(18, 60)

    def _generate_motif(self, gravity: str) -> str:
        """Sélectionne un motif de consultation selon la gravité."""
        motifs_map = {
            "GRIS": self.MOTIFS_GRIS,
            "VERT": self.MOTIFS_VERT,
            "JAUNE": self.MOTIFS_JAUNE,
            "ROUGE": self.MOTIFS_ROUGE,
        }
        return random.choice(motifs_map[gravity])

    def _generate_constantes(
        self, gravity: str, age: int
    ) -> ConstantesVitales:
        """
        Génère des constantes vitales réalistes selon la gravité et l'âge.
        """
        # Valeurs de base normales
        fc_base = 70 if age > 12 else 100
        fr_base = 16 if age > 12 else 25
        temp_base = 37.0
        spo2_base = 98
        pa_systolique_base = 120 if age < 60 else 140
        pa_diastolique_base = 80

        # Ajustements selon la gravité
        if gravity == "ROUGE":
            fc = random.randint(fc_base + 30, fc_base + 80)  # Tachycardie sévère
            fr = random.randint(fr_base + 10, fr_base + 20)  # Polypnée
            temp = random.uniform(35.0, 36.0) if random.random() < 0.3 else random.uniform(39.5, 41.0)
            spo2 = random.randint(70, 89)  # Hypoxémie sévère
            pa_systolique = random.randint(70, 90) if random.random() < 0.5 else random.randint(180, 220)
            pa_diastolique = random.randint(40, 60) if pa_systolique < 100 else random.randint(100, 130)
            douleur = random.randint(8, 10)

        elif gravity == "JAUNE":
            fc = random.randint(fc_base + 10, fc_base + 40)
            fr = random.randint(fr_base + 5, fr_base + 12)
            temp = random.uniform(38.5, 39.5) if random.random() < 0.6 else random.uniform(36.0, 37.0)
            spo2 = random.randint(90, 93)
            pa_systolique = random.randint(100, 110) if random.random() < 0.4 else random.randint(160, 180)
            pa_diastolique = random.randint(60, 75) if pa_systolique < 120 else random.randint(90, 100)
            douleur = random.randint(5, 8)

        elif gravity == "VERT":
            fc = random.randint(fc_base - 10, fc_base + 20)
            fr = random.randint(fr_base - 2, fr_base + 5)
            temp = random.uniform(37.5, 38.5) if random.random() < 0.4 else random.uniform(36.5, 37.5)
            spo2 = random.randint(94, 97)
            pa_systolique = random.randint(110, 140)
            pa_diastolique = random.randint(70, 90)
            douleur = random.randint(2, 5)

        else:  # GRIS
            fc = random.randint(fc_base - 10, fc_base + 10)
            fr = random.randint(fr_base - 2, fr_base + 2)
            temp = random.uniform(36.5, 37.5)
            spo2 = random.randint(97, 100)
            pa_systolique = random.randint(110, 130)
            pa_diastolique = random.randint(70, 85)
            douleur = random.randint(0, 2)

        # Glycémie (optionnelle, mesurée dans ~40% des cas)
        glycemie = None
        if random.random() < 0.4:
            if gravity == "ROUGE" and random.random() < 0.3:
                glycemie = random.uniform(0.3, 0.6)  # Hypoglycémie sévère
            elif gravity == "JAUNE" and random.random() < 0.2:
                glycemie = random.uniform(2.5, 4.0)  # Hyperglycémie
            else:
                glycemie = random.uniform(0.7, 1.4)  # Normale

        return ConstantesVitales(
            frequence_cardiaque=int(fc),
            pression_systolique=int(pa_systolique),
            pression_diastolique=int(pa_diastolique),
            frequence_respiratoire=int(fr),
            temperature=round(temp, 1),
            saturation_oxygene=int(spo2),
            echelle_douleur=int(douleur),
            glycemie=round(glycemie, 1) if glycemie else None,
        )

    def _generate_antecedents(self, age: int) -> str:
        """Génère des antécédents médicaux réalistes."""
        antecedents_possibles = [
            "Hypertension artérielle",
            "Diabète type 2",
            "Asthme",
            "BPCO",
            "Insuffisance cardiaque",
            "Coronaropathie",
            "AVC antérieur",
            "Cancer en rémission",
            "Insuffisance rénale",
        ]

        # Plus d'antécédents chez les personnes âgées
        n_antecedents = 1 if age < 40 else random.randint(1, 3)
        return ", ".join(random.sample(antecedents_possibles, n_antecedents))

    def _generate_traitements(self) -> str:
        """Génère des traitements en cours."""
        traitements_possibles = [
            "Antihypertenseur",
            "Antidiabétique oral",
            "Anticoagulant",
            "Bêta-bloquant",
            "Statine",
            "Diurétique",
            "Corticoïde inhalé",
            "Antiagrégant plaquettaire",
        ]

        n_traitements = random.randint(1, 3)
        return ", ".join(random.sample(traitements_possibles, n_traitements))
