"""
RedFlag-AI - Interface Streamlit pour le Triage Médical aux Urgences
Projet Data for Good - M2 SISE

Cette application propose plusieurs modes :
1. SIMULATION : Cas prédéfinis pour démontrer le système
2. INTERACTIF : Chat avec patient simulé pour tester les limites
3. VALIDATION : Validation infirmière des prédictions
4. MODÈLES : Gestion et réentraînement des modèles ML
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.interface.components.simulation_mode import render_simulation_mode
from src.interface.components.interactive_mode import render_interactive_mode
from src.interface.components.metrics_dashboard import render_metrics_dashboard
from src.interface.components.validation_mode import render_validation_mode
from src.interface.components.models_management import render_models_management

# Configuration de la page
st.set_page_config(
    page_title="RedFlag-AI - Triage Médical",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    /* Color coding for triage levels */
    .triage-rouge {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .triage-orange {
        background-color: #ff8800;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .triage-jaune {
        background-color: #ffbb00;
        color: black;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .triage-vert {
        background-color: #00cc66;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .triage-gris {
        background-color: #888888;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Point d'entrée principal de l'application"""

    # Header
    st.markdown('<div class="main-header">🏥 RedFlag-AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Système Intelligent de Triage aux Urgences</div>',
        unsafe_allow_html=True
    )

    # Sidebar - Sélection du mode
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=RedFlag-AI", use_container_width=True)
        st.markdown("---")

        mode = st.radio(
            "Mode d'utilisation",
            options=[
                "Simulation (Cas Prédéfinis)",
                "Interactif (Chat Patient)",
                "Métriques",
                "Validation Infirmière",
                "Gestion Modèles"
            ],
            index=0
        )

        st.markdown("---")
        st.markdown("### À propos")
        st.info("""
        **RedFlag-AI v2.0** - Système de triage basé sur :
        - **Grille FRENCH** officielle (SFMU)
        - **ML** : XGBoost + feedback loop
        - **RAG** : Base documentaire médicale
        - **MLflow** : Versioning des modèles
        """)

        st.markdown("---")
        st.markdown("### 🎓 Projet M2 SISE")
        st.markdown("**Data for Good** - 2025")
        st.markdown("Sujet 1 : Agent de Triage")

    # Contenu principal selon le mode
    if "Simulation" in mode:
        render_simulation_mode()
    elif "Interactif" in mode:
        render_interactive_mode()
    elif "Métriques" in mode:
        render_metrics_dashboard()
    elif "Validation" in mode:
        render_validation_mode()
    elif "Modèles" in mode:
        render_models_management()
    else:
        render_simulation_mode()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #999; font-size: 0.9rem;">'
        '⚕️ RedFlag-AI - Projet Académique - Ne pas utiliser en production'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
