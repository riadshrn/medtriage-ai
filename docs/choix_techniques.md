# 📝 Architecture Decision Records (ADR) - MedTriage AI

## 1. Build & Dépendances : `uv`
* **Problème :** Temps de build Docker prohibitifs avec `pip` à cause des librairies lourdes (torch, XGBoost, sentence-transformers).
* **Solution :** Remplacement de pip par **[uv](https://github.com/astral-sh/uv)** (gestionnaire de paquets écrit en Rust).
* **Gain :** Builds accélérés (x10-x100), gestion du cache Docker optimisée et résolution de dépendances parallélisée.

## 2. Abstraction LLM : `LiteLLM`
* **Problème :** Comme dans le cours de Clovis, l'idée est de pouvoir changer de provider LLM pour les benchmark et adopter celui qui nous correspond le mieux
* **Solution :** Utilisation de **[LiteLLM](https://docs.litellm.ai/)** comme couche d'abstraction unique.
* **Gain :** Changement de modèle (SaaS Mistral/GPT ou Local Ollama) via simple configuration `.env` sans refactoring. Standardisation des formats d'entrée/sortie.

## 3. Observabilité GreenOps : `EcoLogits`
* **Problème :** Nécessité de monitorer l'impact environnemental (CO2/Énergie) caché des requêtes IA générative.
* **Solution :** Intégration d'**[EcoLogits](https://ecologits.ai/)** via son hook natif pour LiteLLM.
* **Gain :** Calcul automatique et temps réel de l'empreinte carbone (`gwp_kgco2`) et énergétique (`energy_kwh`) pour chaque inférence, sans instrumentation manuelle complexe.

## 4. Greenops de la brique agentique
* **Problème :**Ecologits ne se branche pas à pydantic-ai qui nous permet d'instancier l'agent et donc on ne peut que récupérer le nbr de tokens utilisés (et la latence qu'on peut calculer ~)
* **Solution :** Tentative d'estimer la consommation à partir des tokens et la latence --> on a donc implémenté un script calibrate.py qui utilise litellm et ecologits pour calculer la conso d'un modèle donné en paramètre sur 30 prompts de taille variable, pour ensuite extraire une relation CO_2 = a*tokens + b*latence