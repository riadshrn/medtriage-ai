FROM ghcr.io/mlflow/mlflow:v2.10.0

WORKDIR /mlflow

# Sur HF Spaces avec Persistent Storage, /data est persistant
# Sinon les donnees seront perdues au redemarrage
RUN mkdir -p /data/mlflow

EXPOSE 7860

# Utilise /data pour la persistance (si Persistent Storage active)
CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--backend-store-uri", "sqlite:////data/mlflow/mlflow.db", \
     "--default-artifact-root", "/data/mlflow/artifacts"]
