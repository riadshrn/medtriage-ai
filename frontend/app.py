"""
Page d'Accueil - Documentation MedTriage-AI.

Cette page presente le projet MedTriage-AI avec une documentation
complete de l'architecture, des fonctionnalites et des services.
"""

import sys
from pathlib import Path

import streamlit as st

# Config Paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from state import init_session_state
from style import configure_page, apply_style

# IMPORTANT: configure_page DOIT etre appelee EN PREMIER
configure_page(page_title="MedTriage-AI - Documentation")
init_session_state()
apply_style()

# =============================================================================
# PRESENTATION GENERALE
# =============================================================================
st.title("Documentation du Projet")
st.caption("v2.1.0 - Hybrid (FRENCH + ML + Agent PydanticAI + RAG)")

st.info("**Navigation** : Utilisez le menu lateral pour acceder aux fonctionnalites (Accueil, Mode Interactif, Dashboard, etc.)")

# -----------------------------------------------------------------------------
# SECTION 1: QU'EST-CE QUE MEDTRIAGE-AI ?
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Qu'est-ce que MedTriage-AI ?")

    st.markdown("""
    MedTriage-AI est un **systeme hybride intelligent** de triage medical aux urgences qui combine :
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Regles Metier (FRENCH)**
        - Classification SFMU Tri 1-5
        - Detection des red flags
        - Orientation deterministe
        """)

    with col2:
        st.markdown("""
        **Machine Learning (XGBoost)**
        - Prediction adaptable
        - Apprentissage continu
        - Feedback loop
        """)

    with col3:
        st.markdown("""
        **IA Generative (PydanticAI)**
        - Agent copilote
        - RAG avec ChromaDB
        - Monitoring ecologique
        """)

# -----------------------------------------------------------------------------
# SECTION 2: FONCTIONNALITES
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Fonctionnalites Principales")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Accueil - Triage par Conversation**
        - Upload fichiers CSV/TXT
        - Extraction automatique via LLM
        - Classification hybride FRENCH + ML
        - Metriques GreenOps temps reel

        **Mode Interactif - Simulation**
        - Personas patients realistes
        - Entrainement infirmiers IOA
        - Dialogue interactif LLM
        - Validation donnees collectees
        """)

    with col2:
        st.markdown("""
        **Dashboard - Metriques**
        - Cout estime par requete ($)
        - Empreinte CO2 avec analogies
        - Energie consommee (Wh)
        - Historique cumule

        **Feedback & MLFlow**
        - Correction predictions
        - Reentrainement automatique
        - Versioning modeles
        - Promotion en production
        """)

# -----------------------------------------------------------------------------
# SECTION 3: ARCHITECTURE
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Architecture Technique")

    st.code("""
┌─────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE GLOBALE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   FRONTEND (Streamlit:8501)          BACKEND (FastAPI:8000)        │
│   ├─ 0_Accueil.py                    ├─ Routes:                    │
│   ├─ 1_Mode_interactif.py            │   /conversation             │
│   ├─ 2_Dashboard.py                  │   /triage/predict           │
│   ├─ 3_Feedback.py                   │   /feedback                 │
│   ├─ 4_MLFlow.py                     │   /benchmark                │
│   └─ 5_Benchmark.py                  │   /models                   │
│                                      │                              │
│                                      ├─ Services:                   │
│                                      │   extraction_service (LLM)   │
│                                      │   triage_service (FRENCH+ML) │
│                                      │   agent_service (PydanticAI) │
│                                      │   med_tools (RAG ChromaDB)   │
│                                      │                              │
│                                      └─ ML Pipeline:                │
│                                          classifier.py (XGBoost)    │
│                                          trainer.py (MLflow)        │
│                                          feedback_handler.py        │
│                                                                     │
│   MLFLOW (Tracking:5000)                                            │
│   ├─ Experiments & Runs                                             │
│   ├─ Model Registry                                                 │
│   └─ Artifacts Storage                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
    """, language=None)

# -----------------------------------------------------------------------------
# SECTION 4: PIPELINE DE TRAITEMENT
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Pipeline de Traitement")

    st.markdown("""
    **Flux principal d'une requete de triage :**
    """)

    st.code("""
1. UPLOAD                    2. EXTRACTION                   3. TRIAGE
   CSV/TXT                      LLM (Mistral)                   FRENCH + ML
   conversation                 JSON structure                  consolidation
        │                            │                              │
        ▼                            ▼                              ▼
┌──────────────┐           ┌──────────────────┐           ┌──────────────────┐
│ Conversation │    ──▶    │ ExtractedPatient │    ──▶    │ TriageResponse   │
│ infirmier/   │           │ age, sexe, motif │           │ gravite: ROUGE   │
│ patient      │           │ constantes       │           │ confiance: 0.92  │
└──────────────┘           │ antecedents      │           │ orientation      │
                           └──────────────────┘           └──────────────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │ LLMMetrics       │
                           │ tokens, latence  │
                           │ cout, CO2        │
                           └──────────────────┘
    """, language=None)

# -----------------------------------------------------------------------------
# SECTION 5: AGENT & RAG
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Agent PydanticAI & Systeme RAG")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Workflow Agent (5 etapes)**

        1. **ANALYSE** - Identification symptomes
        2. **PROTOCOLE** - Recherche RAG ChromaDB
        3. **CLASSIFICATION** - Determination couleur
        4. **VALIDATION** - Completude donnees ML
        5. **REDACTION** - Reponse structuree

        **Securite**: Sandwich Defense contre prompt injection
        """)

    with col2:
        st.markdown("""
        **Base RAG (ChromaDB)**

        - Embedding: `paraphrase-multilingual-MiniLM-L12-v2`
        - Stockage: `data/vector_db/` (persistant)
        - Sources: Protocoles SFMU, guidelines medicaux

        **Tools disponibles:**
        - `search_medical_protocol(symptome)`
        - `check_completeness_for_ml(fields)`
        """)

    st.divider()

    st.markdown("**Estimation GreenOps Agent** (EcoLogits ne capture pas PydanticAI)")

    st.code("""
# Formule calibree par regression (R² = 1.000)
CO2 (mg) = 0.002726 * tokens + 0.180694 * latence_s - 0.0291

# Coefficients pour Mistral Small (datacenter France)
COEFF_TOKENS  = 0.002726  # mg/token
COEFF_LATENCY = 0.180694  # mg/seconde
    """, language="python")

# -----------------------------------------------------------------------------
# SECTION 6: DASHBOARD & METRIQUES
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Dashboard GreenOps/FinOps")

    st.markdown("""
    **Metriques capturees par requete :**
    """)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tokens", "input + output", help="Nombre de tokens envoyes/recus")
    m2.metric("Latence", "ms", help="Temps de reponse LLM")
    m3.metric("Cout", "USD", help="Cout estime selon tarifs Mistral")
    m4.metric("CO2", "g", help="Empreinte carbone via EcoLogits")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Tarification Mistral (2026)**

        | Modele | Input | Output |
        |--------|-------|--------|
        | ministral-3b | $0.04/M | $0.04/M |
        | mistral-small | $0.10/M | $0.30/M |
        | mistral-medium | $0.40/M | $2.00/M |
        | mistral-large | $2.00/M | $6.00/M |
        """)

    with col2:
        st.markdown("""
        **Analogies pour comprendre**

        | Valeur | Equivalent |
        |--------|------------|
        | 0.2g CO2 | 1 recherche Google |
        | 1 Wh | 1 min ampoule 60W |
        | 10g CO2 | 100m voiture |
        """)

# -----------------------------------------------------------------------------
# SECTION 7: MLFLOW & FEEDBACK
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("MLFlow & Systeme de Feedback")

    st.markdown("""
    **Cycle de vie du modele ML :**
    """)

    st.code("""
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Training   │────▶│   MLflow    │────▶│  Registry   │────▶│ Production  │
│  XGBoost    │     │  Tracking   │     │  Staging    │     │   Deploy    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    Metriques trackees:
                    - accuracy, f1_macro
                    - precision, recall
                    - cv_accuracy_mean
                    - latency_per_sample
    """, language=None)

    st.divider()

    st.markdown("**Feedback Loop**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Types de correction:**

        | Type | Description |
        |------|-------------|
        | `correct` | Prediction validee |
        | `upgrade` | Sous-estimation (VERT→JAUNE) |
        | `downgrade` | Sur-estimation (JAUNE→VERT) |
        | `disagree` | Completement faux |
        """)

    with col2:
        st.markdown("""
        **Declencheurs:**

        - **100+ feedbacks** → Alerte reentrainement
        - **error_rate > 15%** → Alerte qualite
        - Reentrainement manuel ou via API

        **Stockage:** `data/feedback/nurse_feedback.jsonl`
        """)

# -----------------------------------------------------------------------------
# SECTION 8: BENCHMARKS
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Benchmarks Eco-Performance")

    st.markdown("""
    **Comparaison des modeles Mistral** sur 3 axes : Qualite / Cout / Ecologie
    """)

    st.code("""
┌───────────────────┬──────────┬───────────┬──────────┬──────────┐
│ Modele            │ Latence  │ Cout      │ CO2      │ Qualite  │
├───────────────────┼──────────┼───────────┼──────────┼──────────┤
│ ministral-3b      │ 250ms    │ $0.0008   │ 0.15g    │ 78%      │
│ mistral-small     │ 500ms    │ $0.0020   │ 0.40g    │ 92%      │ ◀─ CHOIX
│ mistral-medium    │ 800ms    │ $0.0080   │ 0.80g    │ 95%      │
│ mistral-large     │ 1200ms   │ $0.0160   │ 1.60g    │ 97%      │
└───────────────────┴──────────┴───────────┴──────────┴──────────┘

Recommandation: mistral-small = meilleur compromis qualite/cout/ecologie
    """, language=None)

# -----------------------------------------------------------------------------
# SECTION 9: STRUCTURE DES DOSSIERS
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Structure du Projet")

    with st.expander("Voir la structure complete des dossiers"):
        st.code("""
medtriage/
├── docker-compose.yml          # Orchestration 3 services
├── .env                        # Variables d'environnement
│
├── backend/
│   ├── api/
│   │   ├── main.py             # Point d'entree FastAPI
│   │   ├── routes/             # Controleurs HTTP
│   │   │   ├── conversation.py # Upload + Process
│   │   │   ├── triage.py       # Prediction directe
│   │   │   ├── feedback.py     # Feedback loop
│   │   │   ├── benchmark.py    # Benchmarks modeles
│   │   │   └── mlflow_routes.py# Model Registry
│   │   │
│   │   ├── services/           # Logique metier
│   │   │   ├── extraction_service.py  # LLM + EcoLogits
│   │   │   ├── triage_service.py      # FRENCH + ML
│   │   │   ├── agent_service.py       # PydanticAI
│   │   │   ├── med_tools.py           # RAG ChromaDB
│   │   │   └── french_triage.py       # Regles SFMU
│   │   │
│   │   ├── ml/                 # Pipeline ML
│   │   │   ├── classifier.py   # XGBoost wrapper
│   │   │   ├── feature_config.py # Single Source of Truth
│   │   │   ├── trainer.py      # MLflow integration
│   │   │   └── feedback_handler.py
│   │   │
│   │   ├── schemas/            # Validation Pydantic
│   │   │
│   │   └── data/
│   │       ├── raw/conversations/  # Cas de test
│   │       ├── vector_db/          # ChromaDB (RAG)
│   │       ├── feedback/           # Feedback JSONL
│   │       └── history.json        # Historique triages
│   │
│   └── models/trained/         # Modele XGBoost
│
├── frontend/
│   ├── app.py                  # Cette page (documentation)
│   ├── pages/                  # Pages Streamlit
│   ├── state.py                # Session management
│   └── style.py                # CSS moderne
│
└── mlflow/                     # MLflow server
        """, language=None)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.divider()

st.markdown("""
**Navigation Rapide**

| Page | Description |
|------|-------------|
| **Accueil** | Triage par conversation (upload CSV/TXT) |
| **Mode Interactif** | Simulation patient avec personas |
| **Dashboard** | Metriques GreenOps/FinOps |
| **Feedback** | Historique et corrections infirmiers |
| **MLFlow** | Suivi et promotion des modeles ML |
| **Benchmark** | Comparaison eco-performance modeles |
""")

st.success("Utilisez le **menu lateral** a gauche pour naviguer entre les fonctionnalites.")
