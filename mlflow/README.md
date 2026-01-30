---
title: MedTriage MLflow
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# MLflow Tracking Server

Serveur MLflow pour MedTriage-AI.

## Activer la Persistance

Pour que les donnees MLflow persistent:

1. Allez dans **Settings** de votre Space
2. Activez **Persistent Storage** (payant ~$5/mois)
3. Le dossier `/data` sera persistant

Sans Persistent Storage, les donnees seront perdues au redemarrage.

## URL d'acces

Apres deploiement:
```
https://VOTRE_USERNAME-medtriage-mlflow.hf.space
```

## Configurer le Backend

Dans les Secrets du Space Backend:
```
MLFLOW_TRACKING_URI=https://VOTRE_USERNAME-medtriage-mlflow.hf.space
```

## Alternative gratuite

Si vous ne voulez pas payer pour le Persistent Storage:
- Utilisez MLflow uniquement en local (docker-compose)
- Ou utilisez Databricks Community Edition (gratuit)
