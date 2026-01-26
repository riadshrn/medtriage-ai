### Sprint Final MedTriage

On divise le travail pour éviter les conflits Git. Chacun sa branche, chacun ses fichiers.

#### 🧑‍💻 1 : Backend ML & RAG
* **Objectif :** Fiabiliser le moteur de décision et préparer la base de connaissances pour l'Agent.
* **Tâches :**
    1.  **Refactor ML :** Corrige l'appel XGBoost dans `triage_service.py` (c'est instable). Idéalement, exporte le modèle proprement sur Hugging Face ou en `.json` pour qu'on arrête de le ré-entraîner à chaque build.
    2.  **Backend RAG :** Implémente une fonction RAG simple (`rag_service.py`) qui cherche dans la grille French/Docs médicaux. J'ai besoin de cette fonction pour mon Agent.
* **Branche Git :** `fix/ml-rag-backend`

#### 2 : Dashboard & Impact
* **Objectif :** Rendre les indicateurs écologiques "sexy" et compréhensibles.
* **Tâches :**
    1.  **Dashboard Upgrade :** Dans `2_Dashboard.py`, ajoute des analogies concrètes (ex: "X gCO2 = Y minutes d'ampoule allumée" ou "Z km en voiture").
    2.  **Transparence :** Ajoute les sources des prix en tooltip (ex: "Basé sur Mistral Small: $0.1/M tokens").
    3.  **Documentation :** Commence la structure du Rapport final et le `README.md` en s'appuyant sur nos choix techniques.
* **Branche Git :** `feature/greenops-ui`

#### 3 : Benchmark Modèles
* **Objectif :** Prouver par la data qu'on a choisi le bon modèle (Mistral).
* **Tâches :**
    1.  **Scripting :** Fais un script à part (`benchmark.py`) qui lance notre pipeline sur 10-20 cas patients avec différents modèles (Mistral, GPT-3.5, etc.).
    2.  **Analyse :** Produis un tableau comparatif (Temps / Coût / Qualité) pour le rapport.
    3.  **État de l'art :** Trouve des benchmarks officiels sur Hugging Face (Open LLM Leaderboard) pour comparer nos résultats théoriques.
* **Branche Git :** `chore/benchmark-docs`

####  4 : Simulation & Agent
* **Objectif :** Intégrer la brique "Agentique" demandée.
* **Tâches :**
    1.  Je m'occupe de la page de simulation interactive (Patient vs Infirmier).
    2.  Je crée l'Agent IA qui utilisera le RAG de [Collab A] pour assister l'infirmier en temps réel.
* **Branche Git :** `feature/simulation-agent`