---
title: MedTriage API
emoji: 🏥
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# MedTriage-AI Backend API

API FastAPI pour le triage medical intelligent.

## Endpoints

- `GET /` - Status de l'API
- `GET /health` - Health check
- `POST /triage/predict` - Prediction de triage
- `POST /conversation/upload` - Upload de fichier conversation
- `POST /conversation/agent-audit` - Analyse par agent IA
- `GET /models/list` - Liste des modeles MLflow
- `GET /models/latest` - Dernier modele en production

## Secrets HF Spaces

| Secret | Description |
|--------|-------------|
| `MISTRAL_API_KEY` | Cle API Mistral AI |
| `LLM_MODEL` | Modele LLM (default: mistral/mistral-small-latest) |
| `MLFLOW_TRACKING_URI` | URL du serveur MLflow externe |

## Architecture

Backend de l'application MedTriage-AI deployee sur deux Spaces:
1. **Backend (ce Space)** - API FastAPI + ML + MLflow
2. **Frontend** - Interface Streamlit
