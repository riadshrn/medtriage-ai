---
title: MedTriage UI
emoji: 🏥
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# MedTriage-AI Frontend

Interface Streamlit pour le triage medical intelligent.

## Secrets HF Spaces

| Secret | Description |
|--------|-------------|
| `API_URL` | URL du Space Backend (ex: https://username-medtriage-api.hf.space) |

## Pages

- **Accueil** - Upload de conversations et analyse par IA
- **Test** - Interface de test manuel
- **Dashboard** - Metriques et monitoring

## Architecture

Frontend de l'application MedTriage-AI deployee sur deux Spaces:
1. **Backend** - API FastAPI + ML + MLflow
2. **Frontend (ce Space)** - Interface Streamlit
