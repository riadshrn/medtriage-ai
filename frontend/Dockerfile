FROM python:3.11-slim

# Dependances systeme
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dependances Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le code source
COPY . .

# Correction Streamlit Permissions (important pour HF Spaces)
RUN mkdir -p /tmp/.streamlit && \
    echo "[browser]\ngatherUsageStats = false\n[server]\nheadless = true" > /tmp/.streamlit/config.toml

# Variables d'environnement
ENV HOME=/tmp

# Port HF Spaces (7860 requis)
EXPOSE 7860

# Lancement Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
