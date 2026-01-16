# 🏥 RedFlag-AI - Interface Streamlit

Interface utilisateur pour le système de triage médical intelligent RedFlag-AI.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Lancement de l'application](#lancement-de-lapplication)
- [Modes d'utilisation](#modes-dutilisation)
- [Architecture](#architecture)
- [Tests](#tests)
- [Résolution de problèmes](#résolution-de-problèmes)

---

## 🎯 Vue d'ensemble

L'interface Streamlit de RedFlag-AI propose **trois modes** complémentaires :

### 1. 🎬 Mode Simulation (Cas Prédéfinis)
- **Objectif** : Démontrer le système dans des conditions contrôlées
- **Utilisation** : Sélectionnez parmi 10+ cas cliniques réalistes
- **Couverture** : Tous les niveaux de gravité (Rouge, Orange, Jaune, Vert, Gris)
- **Cas spéciaux** : Edge cases avec constantes contradictoires

### 2. 💬 Mode Interactif (Chat Patient)
- **Objectif** : Tester le système avec un patient simulé
- **Utilisation** : Jouez le rôle de l'infirmier(e) de triage
- **Fonctionnalités** :
  - Conversation avec patient LLM-simulé
  - Prise de constantes vitales
  - Triage en temps réel
  - Analyse pédagogique des résultats

### 3. 📊 Mode Métriques (Dashboard)
- **Objectif** : Évaluer les performances globales du système
- **Métriques** :
  - **Accuracy** : Taux de classification correcte
  - **Latence** : Temps de réponse (ML vs LLM)
  - **Distribution** : Répartition des niveaux
  - **Sur-triage / Sous-triage** : Risques cliniques
  - **Matrice de confusion**

---

## 🚀 Installation

### Prérequis

```bash
python >= 3.9
pip
```

### Dépendances

```bash
cd /path/to/redflag-ai
pip install -r requirements.txt
```

**Dépendances principales** :
- `streamlit >= 1.28.0`
- `pandas`
- `numpy`
- Dépendances du projet (voir [requirements.txt](../../requirements.txt))

---

## 🎮 Lancement de l'application

### Commande de base

```bash
streamlit run src/interface/app.py
```

L'application sera accessible sur : [http://localhost:8501](http://localhost:8501)

### Options avancées

```bash
# Changer le port
streamlit run src/interface/app.py --server.port 8080

# Mode debug
streamlit run src/interface/app.py --logger.level debug

# Désactiver le rechargement automatique
streamlit run src/interface/app.py --server.runOnSave false
```

---

## 📚 Modes d'utilisation

### Mode 1 : Simulation (Cas Prédéfinis)

**Cas disponibles** :

#### 🔴 ROUGE (Urgence Vitale)
- Arrêt cardiaque
- Traumatisme crânien sévère

#### 🟠 ORANGE (Urgence)
- Fracture ouverte
- Crise d'asthme sévère

#### 🟡 JAUNE (Peu Urgent)
- Entorse cheville
- Gastro-entérite

#### 🟢 VERT (Non Urgent)
- Plaie superficielle

#### ⚪ GRIS (Consultation Mineure)
- Petite écorchure

#### ⚠️ EDGE CASES
- Constantes contradictoires
- Patient anxieux (simulation crise de panique)

**Workflow** :

1. Sélectionnez un cas clinique
2. Activez/désactivez RAG selon besoins
3. Lancez le triage
4. Analysez les résultats :
   - Niveau attendu vs obtenu
   - Justification clinique
   - Métriques de performance
   - Recommandations

**Capture d'écran** :

```
┌────────────────────────────────────────┐
│  📋 Patient : 65 ans                   │
│  Motif : Douleur thoracique intense    │
│  Gravité attendue : 🔴 ROUGE           │
├────────────────────────────────────────┤
│  🩺 Constantes Vitales                 │
│  FC: 180 bpm | FR: 8 /min              │
│  SpO2: 75% | Glasgow: 6/15             │
├────────────────────────────────────────┤
│  [🚨 LANCER LE TRIAGE]                 │
└────────────────────────────────────────┘
```

---

### Mode 2 : Interactif (Chat Patient)

**Types de patients simulés** :

1. 🎲 **Aléatoire** : Génération dynamique
2. 🔥 **Urgence Vitale (Rouge)**
3. ⚡ **Urgence (Orange)**
4. ⏰ **Peu Urgent (Jaune)**
5. ✅ **Non Urgent (Vert)**
6. 🧪 **Cas Limite (Edge Case)**
7. 🎭 **Simulation d'Anxiété**
8. 🤥 **Patient Minimisant**
9. 😱 **Patient Exagérant**

**Workflow** :

1. Configurez le type de patient
2. Cliquez sur "Nouveau Patient"
3. Interrogez le patient (conversation)
   - Questions sur les symptômes
   - Durée des symptômes
   - Antécédents médicaux
4. Prenez les constantes vitales (bouton dédié)
5. Lancez le triage final
6. Analysez les résultats + feedback pédagogique

**Exemples de questions** :

```text
👨‍⚕️ Infirmier(e) : "Pouvez-vous me décrire vos symptômes ?"
🤒 Patient : "Oh mon Dieu ! C'est terrible ! Palpitations ! ..."

👨‍⚕️ Infirmier(e) : "Depuis quand avez-vous ces symptômes ?"
🤒 Patient : "Depuis environ 30 minutes... c'est arrivé brutalement..."

👨‍⚕️ Infirmier(e) : "Sur une échelle de 1 à 10, la douleur ?"
🤒 Patient : "10 sur 10 ! C'est insupportable !"
```

**Actions rapides** :

- 🩺 **Prendre les Constantes** : Mesure automatique
- 📋 **Résumer le Cas** : Synthèse de la conversation
- 🚨 **Triage Final** : Lancement de l'analyse complète

---

### Mode 3 : Métriques (Dashboard)

**Configuration du benchmark** :

- Nombre de patients : 10 à 100
- Activer/désactiver RAG
- Lancement automatique

**Métriques affichées** :

#### 🎯 Métriques Principales

| Métrique | Description | Objectif |
|----------|-------------|----------|
| **Accuracy Globale** | Taux de classification correcte | ≥ 90% |
| **Latence Moyenne** | Temps de réponse | < 100 ms |
| **Sur-Triage** | Surestimation de la gravité | < 10% |
| **Sous-Triage** | Sous-estimation de la gravité | < 5% (CRITIQUE) |

#### 📊 Distribution des Niveaux

Comparaison avec la distribution réelle aux urgences :

```
Niveau    Système    Réel
🔴 ROUGE    8%       5-10%
🟠 ORANGE  18%      15-20%
🟡 JAUNE   35%      30-40%
🟢 VERT    30%      25-35%
⚪ GRIS     9%       5-10%
```

#### ⚡ Latences

- **Latence Minimale** : Meilleur cas
- **Latence Moyenne** : Performance typique
- **Latence Maximale** : Pire cas

#### 🔀 ML vs LLM

- **ML (XGBoost)** : Utilisé pour TOUS les cas (décision principale)
- **LLM + RAG** : Utilisé pour enrichir les justifications (si activé)

**Export des résultats** :

- 📥 **JSON** : Données complètes + métadonnées
- 📊 **CSV** : Tableau des prédictions

---

## 🏗️ Architecture

```
src/interface/
├── app.py                          # Point d'entrée principal
├── components/
│   ├── __init__.py
│   ├── simulation_mode.py          # Mode simulation
│   ├── interactive_mode.py         # Mode interactif
│   └── metrics_dashboard.py        # Dashboard métriques
├── utils.py                        # Utilitaires et validation
└── README.md                       # Ce fichier

tests/interface/
├── __init__.py
├── test_simulation_mode.py         # Tests mode simulation
├── test_interactive_mode.py        # Tests mode interactif
├── test_metrics_dashboard.py       # Tests dashboard
└── test_utils.py                   # Tests utilitaires
```

### Composants clés

#### `app.py`
- Configuration Streamlit
- Sélection du mode (sidebar)
- Routing vers les composants

#### `simulation_mode.py`
- 10+ cas prédéfinis couvrant tous les niveaux
- Validation des résultats (attendu vs obtenu)
- Affichage des métriques de performance

#### `interactive_mode.py`
- Génération de personas patients
- Simulation de conversation (rule-based)
- Prise de constantes vitales
- Triage + feedback pédagogique

#### `metrics_dashboard.py`
- Génération de patients de test
- Benchmark automatique (10-100 patients)
- Calcul de métriques métier
- Visualisations et export

#### `utils.py`
- Validation des données patient
- Vérification de cohérence physiologique
- Gestion des erreurs
- Formatage des résultats

---

## 🧪 Tests

### Lancer tous les tests de l'interface

```bash
cd /path/to/redflag-ai

# Tous les tests
python -m pytest tests/interface/ -v

# Tests spécifiques
python -m pytest tests/interface/test_simulation_mode.py -v
python -m pytest tests/interface/test_interactive_mode.py -v
python -m pytest tests/interface/test_metrics_dashboard.py -v
python -m pytest tests/interface/test_utils.py -v
```

### Tests unitaires

**Total : 50+ tests**

#### Simulation Mode (15 tests)
- Validation des cas prédéfinis
- Couverture de tous les niveaux
- Tests de triage (Rouge, Orange, etc.)
- Gestion des edge cases
- Plages de constantes réalistes

#### Interactive Mode (20 tests)
- Génération de personas
- Messages initiaux selon gravité
- Réponses adaptées à la personnalité
- Validation de complétude des constantes

#### Metrics Dashboard (10 tests)
- Génération de patients de test
- Calcul d'accuracy
- Tracking de latence
- Détection sur/sous-triage
- Matrice de confusion

#### Utils (15 tests)
- Validation des données patient
- Détection d'incohérences physiologiques
- Formatage des résultats
- Calcul de métriques agrégées

### Coverage

```bash
# Générer un rapport de couverture
python -m pytest tests/interface/ --cov=src/interface --cov-report=html

# Ouvrir le rapport
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

---

## 🎓 Utilisation pour le Projet Académique

### Démonstration Recommandée

**1. Introduction (5 min)**
- Présenter l'interface et les 3 modes
- Expliquer la problématique du triage

**2. Mode Simulation (10 min)**
- Montrer 3-4 cas :
  - 🔴 Rouge : Arrêt cardiaque (urgence vitale)
  - 🟠 Orange : Fracture ouverte
  - 🟡 Jaune : Gastro-entérite
  - ⚠️ Edge Case : Constantes contradictoires
- Commenter les résultats, justifications, latences

**3. Mode Interactif (10 min)**
- Créer un patient aléatoire ou spécifique
- Simuler une consultation de triage
- Montrer la prise de constantes
- Analyser le résultat final
- Insister sur le feedback pédagogique

**4. Mode Métriques (10 min)**
- Lancer un benchmark (50 patients)
- Analyser :
  - Accuracy ≥ 90% (objectif clinique)
  - Latence < 100ms (urgences)
  - Sous-triage < 5% (sécurité)
  - Distribution réaliste
- Montrer l'export JSON/CSV

**5. Discussion (5 min)**
- Forces : Accuracy, Latence, Justifications
- Limites : Edge cases, Besoin validation humaine
- Perspectives : Enrichissement RAG, Fine-tuning

### Questions Attendues

**Q : Pourquoi 3 modes ?**
> R : Mode Simulation pour la démo contrôlée, Mode Interactif pour tester les limites (comme demandé), Mode Métriques pour l'évaluation quantitative.

**Q : Comment gérez-vous les cas limites ?**
> R : Edge cases prédéfinis + patients avec personnalités extrêmes (anxieux, minimisant) pour tester la robustesse.

**Q : Pourquoi combiner ML et LLM ?**
> R : ML (XGBoost) pour la décision rapide et fiable (99% accuracy). LLM+RAG pour les justifications contextuelles enrichies (explicabilité).

**Q : Le système peut-il remplacer un infirmier ?**
> R : Non, c'est un **outil d'aide à la décision**. Le jugement humain reste essentiel, surtout pour les edge cases.

**Q : Quelle est la métrique la plus importante ?**
> R : Le **taux de sous-triage** (< 5%). Un patient grave classé à tort comme non urgent est CRITIQUE. Le sur-triage est moins dangereux.

---

## 🔧 Résolution de problèmes

### L'application ne démarre pas

**Erreur : `ModuleNotFoundError`**

```bash
# Solution : Installer les dépendances
pip install -r requirements.txt
```

**Erreur : `FileNotFoundError: data/models/...`**

```bash
# Solution : Générer les modèles d'abord
python scripts/train_models.py
```

### L'interface est lente

**Latence élevée (> 500ms)**

- Désactiver RAG pour des tests plus rapides
- Vérifier que les modèles sont bien chargés
- Réduire le nombre de patients dans le benchmark

### Les résultats sont incorrects

**Accuracy faible (< 80%)**

- Vérifier la qualité des données d'entraînement
- Réentraîner le modèle ML : `python scripts/train_models.py`
- Vérifier les seuils de décision dans `TriageAgent`

### Erreurs de validation

**"Constantes hors limites"**

- Vérifier les plages dans `utils.validate_patient_data()`
- Les plages sont volontairement larges pour capturer les cas extrêmes

### Mode interactif bloque

**Le chat ne répond pas**

- Vérifier que `generate_patient_response()` fonctionne
- Les réponses sont rule-based (pas de LLM externe requis)

---

## 📖 Ressources Supplémentaires

- **Documentation Streamlit** : https://docs.streamlit.io
- **Guide TriageAgent** : [../agents/README.md](../agents/README.md)
- **Cahier des charges** : [../../Projet_Support.pdf](../../Projet_Support.pdf)

---

## 👥 Contributeurs

**Projet M2 SISE - Data for Good 2025**

Interface développée par Claude Code pour le système RedFlag-AI.

---

## 📄 Licence

Ce projet est académique et destiné à un usage éducatif uniquement.

⚕️ **AVERTISSEMENT** : Ne pas utiliser en production clinique sans validation médicale et réglementaire.
