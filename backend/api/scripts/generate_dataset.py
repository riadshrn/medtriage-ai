"""
Script de génération du dataset d'entraînement.

Usage:
    python scripts/generate_dataset.py --n_samples 1000 --output data/raw/patients_synthetic.csv
"""

import argparse
import csv
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.data import PatientGenerator, GravityLabeler


def main():
    parser = argparse.ArgumentParser(
        description="Génère un dataset de patients synthétiques"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=1000,
        help="Nombre de patients à générer (défaut: 1000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/patients_synthetic.csv",
        help="Fichier de sortie (défaut: data/raw/patients_synthetic.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Graine aléatoire (défaut: 42)",
    )
    args = parser.parse_args()

    print(f"Generation de {args.n_samples} patients synthetiques...")
    print(f"Graine aleatoire : {args.seed}")

    # Génération des patients
    generator = PatientGenerator(seed=args.seed)
    patients = generator.generate_dataset(n_samples=args.n_samples)

    # Attribution des niveaux de gravité
    print("Attribution des niveaux de gravite...")
    labeler = GravityLabeler()
    labeled_data = []

    for patient in patients:
        gravity_level = labeler.label_patient(patient)
        labeled_data.append({
            "id": patient.id,
            "age": patient.age,
            "sexe": patient.sexe,
            "motif_consultation": patient.motif_consultation,
            "frequence_cardiaque": patient.constantes.frequence_cardiaque,
            "pression_systolique": patient.constantes.pression_systolique,
            "pression_diastolique": patient.constantes.pression_diastolique,
            "frequence_respiratoire": patient.constantes.frequence_respiratoire,
            "temperature": patient.constantes.temperature,
            "saturation_oxygene": patient.constantes.saturation_oxygene,
            "echelle_douleur": patient.constantes.echelle_douleur,
            "glycemie": patient.constantes.glycemie or "",
            "antecedents": patient.antecedents or "",
            "traitements_en_cours": patient.traitements_en_cours or "",
            "gravity_level": gravity_level.value,
        })

    # Sauvegarde dans un fichier CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(labeled_data[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(labeled_data)

    print(f"Dataset genere : {output_path}")

    # Statistiques
    print("\nStatistiques du dataset :")
    gravity_counts = {}
    for item in labeled_data:
        level = item["gravity_level"]
        gravity_counts[level] = gravity_counts.get(level, 0) + 1

    for level in ["GRIS", "VERT", "JAUNE", "ROUGE"]:
        count = gravity_counts.get(level, 0)
        percentage = (count / args.n_samples) * 100
        print(f"   {level:6} : {count:4} patients ({percentage:5.1f}%)")


if __name__ == "__main__":
    main()
