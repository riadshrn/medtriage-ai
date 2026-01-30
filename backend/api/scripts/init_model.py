import os
import sys
from pathlib import Path

# On ajoute la racine au path pour les imports
sys.path.append("/app")

def main():
    print("[INIT] Verification des modeles...")
    model_path = Path("models/trained/triage_model.json")
    csv_path = Path("data/raw/patients_synthetic.csv")

    # 1. Verif Modele
    if model_path.exists() and not os.getenv("FORCE_RETRAIN"):
        print("[INIT] Modele present. Pret a demarrer.")
        return

    print("[INIT] Modele manquant. Lancement du Cold Start...")

    # 2. Verif Donnees
    if not csv_path.exists():
        print("[INIT] Generation des donnees...")
        res = os.system("python api/scripts/generate_dataset.py --n_samples 1000 --output data/raw/patients_synthetic.csv")
        if res != 0:
            print("[INIT] Erreur generation donnees.")
            return

    # 3. Entrainement
    print("[INIT] Entrainement du modele...")
    res = os.system("python api/scripts/train_model.py --data data/raw/patients_synthetic.csv --output models/trained")

    if res == 0:
        print("[INIT] Cold Start termine avec succes.")
    else:
        print("[INIT] Echec de l'entrainement.")

if __name__ == "__main__":
    main()
