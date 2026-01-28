"""
Script d'entraînement du modèle de classification.

Usage:
    python scripts/train_model.py --data data/raw/patients_synthetic.csv --output models/trained
"""
import argparse
from pathlib import Path
import sys
# On s'assure que Python voit la racine /app
sys.path.append("/app") 

# On pointe vers le NOUVEL emplacement
from api.ml import ModelTrainer, ModelEvaluator
from api.ml.preprocessor import TriagePreprocessor


def main():
    parser = argparse.ArgumentParser(
        description="Entraine le modele de classification de triage"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/raw/patients_synthetic.csv",
        help="Chemin vers le CSV de donnees (defaut: data/raw/patients_synthetic.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/trained",
        help="Dossier de sortie pour le modele (defaut: models/trained)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion du test set (defaut: 0.2)",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Nombre d'arbres XGBoost (defaut: 100)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Profondeur maximale des arbres (defaut: 6)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.1,
        help="Taux d'apprentissage (defaut: 0.1)",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Nombre de folds pour la validation croisee (defaut: 5)",
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Activer la recherche d'hyperparametres",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Graine aleatoire (defaut: 42)",
    )
    args = parser.parse_args()

    # Vérification de l'existence du fichier de données
    if not Path(args.data).exists():
        print(f"Erreur : Le fichier {args.data} n'existe pas.")
        print("Veuillez d'abord generer le dataset avec :")
        print("  python scripts/generate_dataset.py")
        sys.exit(1)

    # Création du trainer
    trainer = ModelTrainer(random_state=args.seed)

    # Entraînement
    if args.tune:
        print("Mode : Hyperparameter tuning")
        classifier = trainer.train_with_tuning(
            csv_path=args.data,
            test_size=args.test_size,
            cv_folds=args.cv_folds,
        )
    else:
        print("Mode : Entrainement standard")
        classifier = trainer.train_from_csv(
            csv_path=args.data,
            test_size=args.test_size,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            cv_folds=args.cv_folds,
        )

    # Évaluation complète
    df = trainer.preprocessor.load_data(args.data)
    X_train, X_test, y_train, y_test = trainer.preprocessor.prepare_train_test(
        df, test_size=args.test_size, random_state=args.seed
    )

    ModelEvaluator.print_evaluation(classifier, X_test, y_test)

    # Sauvegarde du modèle
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "triage_model.json"
    preprocessor_path = output_dir / "preprocessor.pkl"

    classifier.save(str(model_path), str(preprocessor_path))

    print("\nModele sauvegarde avec succes !")
    print(f"  Modele        : {model_path}")
    print(f"  Preprocesseur : {preprocessor_path}")


if __name__ == "__main__":
    main()
