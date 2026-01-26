# 🏗️ Architecture Technique - Projet MedTriage AI

Ce document détaille la structure du code et la responsabilité de chaque module. L'architecture suit une séparation stricte entre la couche de présentation (Frontend), la couche de contrôle (Routes) et la couche métier (Services).

## 1. Infrastructure & Orchestration

* **`docker-compose.yml`** : Orchestration des conteneurs.
    * Définit deux services : `api` (Backend) et `ui` (Frontend).
    * Gère le montage des volumes (`./src:/app/src`) pour le *hot-reloading* en développement.
    * Gère le réseau interne pour la communication `ui` -> `api`.
* **`.env`** : Configuration des variables d'environnement (Clés API Mistral/OpenAI, configuration EcoLogits, URLs).

---

## 2. Backend (`src/api`) - FastAPI

Le backend expose une API RESTful typée.

### 📂 `routes/` (Contrôleurs)
Responsable de la réception des requêtes HTTP, de la validation des entrées et de la réponse formatée. Ne contient **aucune logique métier complexe**.

* **`conversation.py`** :
    * `POST /upload` : Gère le parsing des fichiers CSV/TXT vers un format JSON standardisé.
    * `POST /process` : Point d'entrée principal. Orchestre l'appel séquentiel aux services (Extraction -> Triage) et retourne un objet `SimulationResult` complet.

### 📂 `services/` (Logique Métier)
Cœur fonctionnel de l'application. Chaque service est indépendant.

* **`extraction_service.py`** : **Interface LLM (Generative AI)**.
    * Utilise `litellm` pour communiquer avec les modèles (Mistral, GPT, Ollama).
    * Intègre `EcoLogits` pour monitorer l'empreinte carbone et énergétique de chaque appel en temps réel.
    * Transforme le texte brut en données structurées via Pydantic (Extraction d'entités médicales).
* **`triage_service.py`** : **Moteur de décision (Predictive AI)**.
    * Implémente l'algorithme "French Emergency Nurses Classification" (règles métiers).
    * Charge le modèle Machine Learning (XGBoost) via `models/trained/`.
    * Combine les règles et la prédiction ML pour fournir un score de gravité et de confiance.

### 📂 `schemas/` (Data Transfer Objects)
Définitions Pydantic pour la validation stricte des données (Typage fort).

* **`extraction.py`** : Structure attendue en sortie du LLM (Patient, Constantes, Antécédents).
* **`triage.py`** : Structure d'entrée pour le moteur de triage (Normalisation des données).
* **`monitoring.py`** : Structure des métriques FinOps/GreenOps (Coûts, Latence, CO2).

---

## 3. Frontend (`src/interface`) - Streamlit

Interface utilisateur "Stateless" qui consomme l'API.

* **`app.py`** : Point d'entrée, gestion de la navigation et configuration globale de la page.
* **`state.py`** : Gestion de la persistance de session (`st.session_state`). Permet de conserver les données (chat, résultats d'analyse) lors de la navigation entre les pages.
* **`pages/`** :
    * **`0_Accueil.py`** : Upload de fichier, affichage de la conversation (Chat UI), et déclenchement de l'analyse.
    * **`2_Dashboard.py`** : Visualisation des KPIs techniques (Latence, Tokens, Empreinte Carbone) basés sur la dernière requête.

---

## 🔄 Flux de Données (Pipeline `/process`)

1.  **Input** : Le JSON de la conversation est reçu par la Route.
2.  **Extraction** : Le `ExtractionService` appelle le LLM.
    * *Input* : Transcript brut.
    * *Output* : JSON structuré (Age, Douleur, Constantes) + Métriques EcoLogits.
3.  **Triage** : Le `TriageService` reçoit le JSON structuré.
    * Il applique les règles métiers.
    * Il encode les features et interroge le modèle XGBoost.
4.  **Output** : L'API renvoie un objet unique contenant :
    * Les données extraites.
    * Le résultat du triage (Gravité, Orientation).
    * Les métriques de performance et d'écologie.