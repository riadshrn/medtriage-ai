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

# Dependances systeme pour ChromaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installation des dependances
COPY requirements.txt .

# Fix pour Griffe/Pydantic-AI
RUN uv pip install --no-cache-dir "griffe==1.5.1"

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --index-strategy unsafe-best-match -r requirements.txt

# Pre-telechargement du modele d'embedding (cache)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Copie du code source
COPY api/ ./api/
COPY models/ ./models/
COPY data/ ./data/

# Port HF Spaces (7860 requis)
EXPOSE 7860

# Commande de demarrage
CMD python api/scripts/init_model.py && \
    uvicorn api.main:app --host 0.0.0.0 --port 7860
