# RedFlag-AI - Dockerfile
# Système d'aide au triage des patients aux urgences

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="RedFlag-AI Team"
LABEL description="Système intelligent de triage des patients aux urgences"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY docs/ ./docs/

# Création des répertoires de données
RUN mkdir -p data/raw data/vector_store models/trained

# Exposition du port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande par défaut (Streamlit)
CMD ["streamlit", "run", "src/interface/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
