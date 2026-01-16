"""
Script pour exécuter un triage avec l'agent.

Usage:
    python scripts/run_triage.py --patient-id random
    python scripts/run_triage.py --age 70 --fc 125 --spo2 88 --motif "Difficulté respiratoire"
"""

import argparse
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import TriageAgent
from src.models import Patient, ConstantesVitales
from src.data import PatientGenerator


def create_patient_from_args(args) -> Patient:
    """
    Crée un patient à partir des arguments CLI.

    Args:
        args: Arguments parsés

    Returns:
        Patient: Patient créé
    """
    if args.patient_id == "random":
        # Génération d'un patient aléatoire
        generator = PatientGenerator(seed=None)
        patient = generator.generate_patient()
        return patient

    # Création manuelle
    constantes = ConstantesVitales(
        frequence_cardiaque=args.fc,
        pression_systolique=args.pa_sys,
        pression_diastolique=args.pa_dia,
        frequence_respiratoire=args.fr,
        temperature=args.temp,
        saturation_oxygene=args.spo2,
        echelle_douleur=args.douleur,
        glycemie=args.glycemie,
    )

    patient = Patient(
        age=args.age,
        sexe=args.sexe,
        motif_consultation=args.motif,
        constantes=constantes,
        antecedents=args.antecedents,
    )

    return patient


def main():
    parser = argparse.ArgumentParser(
        description="Execute un triage avec l'agent intelligent"
    )

    # Modèles
    parser.add_argument(
        "--ml-model",
        type=str,
        default="models/trained/triage_model.json",
        help="Chemin vers le modele ML",
    )
    parser.add_argument(
        "--preprocessor",
        type=str,
        default="models/trained/preprocessor.pkl",
        help="Chemin vers le preprocesseur",
    )
    parser.add_argument(
        "--vector-store",
        type=str,
        default="data/vector_store/medical_kb",
        help="Chemin vers le vector store",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Desactiver le RAG (utiliser justifications basees sur regles)",
    )

    # Patient prédéfini
    parser.add_argument(
        "--patient-id",
        type=str,
        default="random",
        help="ID du patient ('random' pour generer aleatoirement)",
    )

    # Données patient (si non aléatoire)
    parser.add_argument("--age", type=int, default=45, help="Age du patient")
    parser.add_argument(
        "--sexe", type=str, default="M", choices=["M", "F", "Autre"], help="Sexe"
    )
    parser.add_argument(
        "--motif", type=str, default="Consultation", help="Motif de consultation"
    )
    parser.add_argument(
        "--fc", type=int, default=80, help="Frequence cardiaque (bpm)"
    )
    parser.add_argument(
        "--pa-sys", type=int, default=120, help="Pression arterielle systolique (mmHg)"
    )
    parser.add_argument(
        "--pa-dia", type=int, default=80, help="Pression arterielle diastolique (mmHg)"
    )
    parser.add_argument("--fr", type=int, default=16, help="Frequence respiratoire")
    parser.add_argument("--temp", type=float, default=37.0, help="Temperature (C)")
    parser.add_argument("--spo2", type=int, default=98, help="Saturation oxygene (pourcent)")
    parser.add_argument(
        "--douleur", type=int, default=0, help="Echelle de douleur (0-10)"
    )
    parser.add_argument("--glycemie", type=float, default=None, help="Glycemie (g/L)")
    parser.add_argument("--antecedents", type=str, default=None, help="Antecedents")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Afficher les details"
    )

    args = parser.parse_args()

    # Vérification des modèles
    if not Path(args.ml_model).exists():
        print(f"Erreur : Modele ML introuvable : {args.ml_model}")
        print("Veuillez d'abord entrainer le modele avec :")
        print("  python scripts/train_model.py")
        sys.exit(1)

    if not Path(args.vector_store + ".faiss").exists() and not args.no_rag:
        print(f"Attention : Vector store introuvable : {args.vector_store}")
        print("Le systeme utilisera des justifications basees sur regles.")
        print("Pour construire la base de connaissances :")
        print("  python scripts/build_knowledge_base.py")
        args.vector_store = None

    # Création du patient
    print("\n" + "=" * 60)
    print("CREATION DU PATIENT")
    print("=" * 60)

    patient = create_patient_from_args(args)

    print(f"\nPatient cree :")
    print(f"  ID               : {patient.id[:8]}...")
    print(f"  Age              : {patient.age} ans")
    print(f"  Sexe             : {patient.sexe}")
    print(f"  Motif            : {patient.motif_consultation}")
    print(f"\nConstantes vitales :")
    print(f"  FC               : {patient.constantes.frequence_cardiaque} bpm")
    print(
        f"  PA               : {patient.constantes.pression_systolique}/{patient.constantes.pression_diastolique} mmHg"
    )
    print(f"  FR               : {patient.constantes.frequence_respiratoire} /min")
    print(f"  Temperature      : {patient.constantes.temperature}°C")
    print(f"  SpO2             : {patient.constantes.saturation_oxygene}%")
    print(f"  Douleur          : {patient.constantes.echelle_douleur}/10")

    # Initialisation de l'agent
    agent = TriageAgent(
        ml_model_path=args.ml_model,
        ml_preprocessor_path=args.preprocessor,
        vector_store_path=args.vector_store,
        use_rag=not args.no_rag,
    )

    # Triage
    result = agent.triage(patient, verbose=args.verbose)

    # Affichage du résultat (si pas déjà affiché en verbose)
    if not args.verbose:
        print("\n" + "=" * 60)
        print("RESULTAT DU TRIAGE")
        print("=" * 60)
        print(f"\nNiveau de gravite : {result.gravity_level.value}")
        print(f"Confiance         : {result.confidence_score:.0%}")
        print(f"\nJustification medicale :")
        print(f"  {result.justification}")
        print(f"\nPerformances :")
        print(f"  Latence ML  : {result.latency_ml * 1000:.2f}ms")
        print(f"  Latence LLM : {result.latency_llm * 1000:.2f}ms")
        print(f"  Total       : {result.total_latency * 1000:.2f}ms")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
