import os
import sys
from pathlib import Path

# On ajoute la racine au path pour les imports
sys.path.append("/app")

def main():
    print("🚀 [INIT] Vérification des modèles...")
    model_path = Path("models/trained/triage_model.json")
    csv_path = Path("data/raw/patients_synthetic.csv")

    # 1. Vérif Modèle
    if model_path.exists() and not os.getenv("FORCE_RETRAIN"):
        print("✅ [INIT] Modèle présent. Prêt à démarrer.")
        return

    print("⚠️ [INIT] Modèle manquant. Lancement du Cold Start...")

    # 2. Vérif Données
    if not csv_path.exists():
        print("🧪 [INIT] Génération des données...")
        # On appelle le script generate_dataset
        # On utilise os.system pour s'assurer que ça tourne dans son propre contexte
        # ou on importe le main() si on a corrigé les imports
        res = os.system("python src/api/scripts/generate_dataset.py --n_samples 1000 --output data/raw/patients_synthetic.csv")
        if res != 0:
            print("❌ [INIT] Erreur génération données.")
            return

    # 3. Entraînement
    print("🧠 [INIT] Entraînement du modèle...")
    res = os.system("python src/api/scripts/train_model.py --data data/raw/patients_synthetic.csv --output models/trained")

    if res == 0:
        print("✅ [INIT] Cold Start terminé avec succès.")
    else:
        print("❌ [INIT] Échec de l'entraînement.")

if __name__ == "__main__":
    main()