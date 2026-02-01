<p align="center">
  <img src="docs/img/logo.png" alt="MedTriage-AI Logo" width="200"/>
</p>

<p align="center">
  <strong>Copilote IA pour le triage médical aux urgences</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.1.0--hybrid-blue?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-Educational-green?style=for-the-badge" alt="License"/>
</p>

<h3 align="center">🚀 Applications Déployées</h3>

<p align="center">
  <a href="https://riadshrn-medtriage-frontend.hf.space/">
    <img src="https://img.shields.io/badge/🖥️_Frontend-Streamlit_App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Frontend"/>
  </a>
  <a href="https://riadshrn-medtriage-backend.hf.space/docs">
    <img src="https://img.shields.io/badge/⚙️_Backend-API_Swagger-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="Backend API"/>
  </a>
  <a href="https://riadshrn-medtriage-mlflow.hf.space/">
    <img src="https://img.shields.io/badge/📊_MLflow-Model_Registry-0194E2?style=for-the-badge&logo=mlflow&logoColor=white" alt="MLflow"/>
  </a>
</p>

<p align="center">
  <em>Hébergé sur</em> <img src="https://img.shields.io/badge/🤗_Hugging_Face_Spaces-FFD21E?style=flat-square" alt="HF"/>
</p>

---

## 🛠️ Technologies Utilisées

### Stack Principal

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

### Intelligence Artificielle & Machine Learning

<p align="center">
  <img src="https://img.shields.io/badge/Mistral_AI-FF7000?style=for-the-badge&logo=mistral&logoColor=white" alt="Mistral AI"/>
  <img src="https://img.shields.io/badge/PydanticAI-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="PydanticAI"/>
  <img src="https://img.shields.io/badge/XGBoost-FF6600?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost"/>
  <img src="https://img.shields.io/badge/LiteLLM-10A37F?style=for-the-badge&logo=openai&logoColor=white" alt="LiteLLM"/>
</p>

### RAG & Vector Database

<p align="center">
  <img src="https://img.shields.io/badge/ChromaDB-FF6B6B?style=for-the-badge&logo=chroma&logoColor=white" alt="ChromaDB"/>
  <img src="https://img.shields.io/badge/🤗_Sentence_Transformers-FFD21E?style=for-the-badge" alt="Sentence Transformers"/>
</p>

### MLOps & Monitoring

<p align="center">
  <img src="https://img.shields.io/badge/MLflow-0194E2?style=for-the-badge&logo=mlflow&logoColor=white" alt="MLflow"/>
  <img src="https://img.shields.io/badge/EcoLogits-22C55E?style=for-the-badge&logo=leaf&logoColor=white" alt="EcoLogits"/>
</p>

### Déploiement

<p align="center">
  <img src="https://img.shields.io/badge/🤗_Hugging_Face_Spaces-FFD21E?style=for-the-badge" alt="HF Spaces"/>
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose"/>
</p>

---

## 📋 À Propos

MedTriage-AI est une application d'aide à la décision pour les infirmiers de régulation médicale. Elle combine :

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| 🤖 **Agent IA** | PydanticAI + Mistral | Analyse et extraction des données cliniques |
| 📚 **RAG** | ChromaDB + MiniLM | Recherche dans les protocoles médicaux |
| 🎯 **ML Classifier** | XGBoost | Classification du niveau de triage |
| 📏 **Règles Expertes** | FRENCH (SFMU) | Standard officiel de triage français |

---

## ✨ Fonctionnalités

### 🏥 Accueil - Régulation Agentique
- Sélection et analyse de conversations patient-infirmier
- Extraction automatique des données structurées (constantes vitales, symptômes, antécédents)
- Classification de criticité (ROUGE, JAUNE, VERT, GRIS) basée sur la grille FRENCH
- Affichage des alertes protocole et informations manquantes
- Traçabilité complète du raisonnement de l'agent (logs RAG + outils)

### 💬 Mode Interactif - Simulation
- Simulation de conversations avec un patient virtuel (LLM)
- Jeu de rôle patient/infirmier : le LLM simule les réponses du patient
- Accumulation des métriques par session de triage
- Possibilité de tester différents scénarios médicaux

### 📊 Dashboard - Pilotage GreenOps / FinOps
- Métriques environnementales en temps réel (CO2, énergie)
- Suivi des coûts par requête LLM
- Statistiques globales persistantes (historique des triages)
- Répartition par niveau de triage et par source
- Analogies parlantes (équivalent recherches Google, minutes d'ampoule 60W)

### 📝 Feedback - Amélioration Continue
- Correction des triages par les experts médicaux
- Alimentation du dataset d'entraînement
- Boucle de rétroaction pour améliorer le modèle ML

### ⚡ Benchmark - Éco-Performance
- Comparaison des modèles Mistral (Ministral 3B, Small, Medium, Large)
- Tests sur 3 cas d'usage : Extraction, Agent Triage, Simulation
- Labels énergétiques (A-E) pour guider le choix du modèle
- Visualisation comparative (énergie, CO2, coût, latence)

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (Streamlit)"]
        A[Accueil]
        B[Mode Interactif]
        C[Dashboard]
        D[Feedback]
        E[Benchmark]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        F[Agent Service<br/>Pydantic-AI]
        G[ML Classifier<br/>XGBoost]
        H[Triage Service<br/>FRENCH]
        I[RAG Tools<br/>ChromaDB]
        J[Preprocessor]
    end

    subgraph External["☁️ Services Externes"]
        K[Mistral API]
        L[MLflow Tracking]
        M[ChromaDB Vector Store]
    end

    Frontend --> Backend
    F --> I
    F --> K
    G --> J
    G --> L
    I --> M
```

---

## 🔧 Choix Techniques

### LLM & Agent

| Composant | Choix | Justification |
|-----------|-------|---------------|
| <img src="https://img.shields.io/badge/Provider-Mistral_AI-FF7000?style=flat-square&logo=mistral&logoColor=white"/> | Mistral AI | Entreprise française, bon rapport qualité/prix |
| <img src="https://img.shields.io/badge/Framework-PydanticAI-E92063?style=flat-square&logo=pydantic&logoColor=white"/> | Pydantic-AI 0.2.4 | Réponses structurées garanties, outils intégrés |
| <img src="https://img.shields.io/badge/Modèle-mistral--small-FF7000?style=flat-square"/> | `mistral-small-latest` | Rapide et économique |

### RAG (Retrieval-Augmented Generation)

| Composant | Choix | Justification |
|-----------|-------|---------------|
| <img src="https://img.shields.io/badge/Vector_Store-ChromaDB-FF6B6B?style=flat-square"/> | ChromaDB | Simple à déployer, stockage persistant |
| <img src="https://img.shields.io/badge/Embeddings-MiniLM--L12-FFD21E?style=flat-square"/> | `paraphrase-multilingual-MiniLM-L12-v2` | Supporte le français (384 dims) |
| <img src="https://img.shields.io/badge/Sources-SFMU-0066CC?style=flat-square"/> | Protocoles SFMU | Référence officielle du triage en France |

### Machine Learning

| Composant | Choix | Justification |
|-----------|-------|---------------|
| <img src="https://img.shields.io/badge/Classifier-XGBoost-FF6600?style=flat-square"/> | XGBoost | Performant et interprétable |
| <img src="https://img.shields.io/badge/Features-11_variables-blue?style=flat-square"/> | Constantes vitales + données patient | Données cliniques standards |
| <img src="https://img.shields.io/badge/MLOps-MLflow_2.10-0194E2?style=flat-square&logo=mlflow&logoColor=white"/> | MLflow | Suivi des modèles et versions |

### GreenOps / Observabilité

| Composant | Choix | Justification |
|-----------|-------|---------------|
| <img src="https://img.shields.io/badge/CO2-EcoLogits-22C55E?style=flat-square"/> | EcoLogits | Standard pour mesurer l'impact des LLM |
| <img src="https://img.shields.io/badge/Mix_Elec-France_🇫🇷-0055A4?style=flat-square"/> | 55g CO2/kWh | Mix électrique français (bas carbone) |
| <img src="https://img.shields.io/badge/Dashboard-Real--time-FF4B4B?style=flat-square"/> | Temps réel + historique | Suivi par requête et sur la durée |

### Infrastructure

| Composant | Choix | Justification |
|-----------|-------|---------------|
| <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/> | FastAPI | Rapide, documentation auto (OpenAPI) |
| <img src="https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/> | Streamlit | Prototypage rapide en Python |
| <img src="https://img.shields.io/badge/Container-Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/> | Docker Compose | Tout-en-un (MLflow + Backend + Frontend) |
| <img src="https://img.shields.io/badge/Build-uv-DE5FE9?style=flat-square"/> | uv | Builds plus rapides que pip |

---

## 🏥 Grille de Triage FRENCH

L'application implémente la grille officielle FRENCH (SFMU - Mars 2018) :

| Niveau | Couleur | Délai | Description |
|--------|---------|-------|-------------|
| Tri 1 | 🔴 **ROUGE** | Sans délai | Détresse vitale majeure |
| Tri 2 | 🔴 **ROUGE** | < 20 min | Atteinte patente |
| Tri 3A | 🟡 **JAUNE** | < 60 min | Atteinte potentielle avec comorbidités |
| Tri 3B | 🟡 **JAUNE** | < 90 min | Atteinte potentielle sans comorbidités |
| Tri 4 | 🟢 **VERT** | < 120 min | Atteinte fonctionnelle stable |
| Tri 5 | ⚪ **GRIS** | < 240 min | Pas d'atteinte évidente |

---

## 📁 Structure du Projet

```
medtriage-ai/
├── 📂 backend/
│   ├── 📂 api/
│   │   ├── routes/          # Endpoints FastAPI
│   │   ├── services/        # Logique métier (agent, triage, ML)
│   │   ├── schemas/         # Modèles Pydantic
│   │   ├── ml/              # Classifieur XGBoost, preprocessing
│   │   └── data/            # Générateur de données, labeling
│   ├── models/              # Modèles ML sauvegardés
│   └── data/                # Base vectorielle ChromaDB
│
├── 📂 frontend/
│   ├── pages/
│   │   ├── 0_Accueil.py          # Régulation agentique
│   │   ├── 1_Mode_interactif.py  # Simulation patient
│   │   ├── 2_Dashboard.py        # GreenOps / FinOps
│   │   ├── 3_Feedback.py         # Correction expert
│   │   ├── 4_MLFlow.py           # Interface MLflow
│   │   └── 5_Benchmark.py        # Comparaison modèles
│   ├── app.py               # Documentation & point d'entrée
│   ├── state.py             # Gestion session_state
│   └── style.py             # Composants UI personnalisés
│
├── 📂 mlflow/               # Configuration MLflow
├── 📂 docs/                 # Documentation technique
└── docker-compose.yml       # Orchestration des services
```

---

## 🚀 Installation

### Prérequis

<p>
  <img src="https://img.shields.io/badge/Docker-Required-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker_Compose-Required-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Mistral_API_Key-Required-FF7000?style=flat-square&logo=mistral&logoColor=white"/>
</p>

### Lancement

```bash
# 1. Cloner le repository
git clone https://github.com/riadshrn/medtriage-ai.git
cd medtriage-ai

# 2. Créer le fichier .env à la racine du projet
echo "MISTRAL_API_KEY=votre_clé_api_ici" > .env
echo "LLM_MODEL=mistral-small-latest" >> .env

# 3. Lancer les services
docker-compose up --build
```

### Accès aux Services

#### 🌐 En Production (Hugging Face Spaces)

| Service | URL |
|---------|-----|
| 🖥️ **Frontend** | [riadshrn-medtriage-frontend.hf.space](https://riadshrn-medtriage-frontend.hf.space/) |
| ⚙️ **Backend API** | [riadshrn-medtriage-backend.hf.space/docs](https://riadshrn-medtriage-backend.hf.space/docs) |
| 📊 **MLflow** | [riadshrn-medtriage-mlflow.hf.space](https://riadshrn-medtriage-mlflow.hf.space/) |

#### 💻 En Local (Docker)

| Service | URL |
|---------|-----|
| 🖥️ **Frontend** | http://localhost:8501 |
| ⚙️ **Backend API** | http://localhost:8000/docs |
| 📊 **MLflow** | http://localhost:5000 |

---

## 🔒 Sécurité

L'agent médical intègre une couche de protection contre les injections de prompt :

| Protection | Description |
|------------|-------------|
| 🥪 **Sandwich Defense** | Les données patient sont encapsulées dans des balises XML `<patient_data>` |
| 🚫 **Blocklist** | 40+ patterns d'injection bloqués (DAN, jailbreak, etc.) |
| ✅ **Validation Pydantic** | Tous les inputs sont validés avec des schémas stricts |

---

## 📈 Métriques & Performances

| Métrique | Valeur | Objectif |
|----------|--------|----------|
| 🎯 Accuracy (ML) | 85-92% | > 80% |
| 📊 F1-Score (macro) | 0.83-0.89 | > 0.80 |
| ⚡ Latence moyenne | < 500ms | < 1s |
| 🌱 CO2 / requête | ~0.003g | Minimiser |

---

## 👥 Auteurs

Projet réalisé dans le cadre du **Master SISE** - Université Lyon 2

- **Riad SAHRANE** 
- **Constantin REY-COQUAIS**
- **Eugénie BARLET**
- **Perrine IBOUROI**

---

## 📄 Licence

Ce projet est à but éducatif. Les protocoles médicaux FRENCH sont la propriété de la SFMU.

