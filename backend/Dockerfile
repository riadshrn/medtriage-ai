FROM python:3.11-slim

# Installation de uv pour des installations plus rapides
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Configuration uv
ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_CACHE_DIR=/root/.cache/uv/
ENV UV_LINK_MODE=copy

# Variables d'environnement par defaut
ENV LLM_MODEL=mistral/mistral-small-latest

# Installation des dependances
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt

# Copie du code source
COPY api/ ./api/
COPY models/ ./models/
COPY data/ ./data/

# Port HF Spaces (7860 requis)
EXPOSE 7860

# Commande de demarrage
CMD python api/scripts/init_model.py && \
    uvicorn api.main:app --host 0.0.0.0 --port 7860
