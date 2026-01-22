"""
RedFlag-AI - Interface Streamlit pour le Triage Médical aux Urgences
Projet Data for Good - M2 SISE

Cette application propose plusieurs modes :
1. SIMULATION : Cas prédéfinis pour démontrer le système
2. INTERACTIF : Chat avec patient simulé pour tester les limites
3. MÉTRIQUES : Dashboard de performance et impact écologique
4. BASE DE CONNAISSANCES : Exploration de la BDD médicale
5. VALIDATION : Validation infirmière des prédictions
6. MODÈLES : Gestion et réentraînement des modèles ML
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
from src.interface.components.knowledge_base import render_knowledge_base

# Configuration de la page
st.set_page_config(
    page_title="RedFlag-AI - Triage Médical Intelligent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé - Design médical moderne
st.markdown("""
<style>
    /* Variables CSS */
    :root {
        --primary-color: #0066cc;
        --secondary-color: #00a878;
        --danger-color: #dc3545;
        --warning-color: #ffc107;
        --success-color: #28a745;
        --background-color: #f8f9fa;
    }

    /* Header principal */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #0066cc 0%, #00a878 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Niveaux de triage - Design moderne */
    .triage-rouge {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
    }

    .triage-orange {
        background: linear-gradient(135deg, #fd7e14 0%, #e8590c 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(253, 126, 20, 0.3);
    }

    .triage-jaune {
        background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
        color: #212529;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
    }

    .triage-vert {
        background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }

    .triage-gris {
        background: linear-gradient(135deg, #6c757d 0%, #545b62 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);
    }

    /* Status badges */
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .status-ok {
        background: #d4edda;
        color: #155724;
    }

    .status-warning {
        background: #fff3cd;
        color: #856404;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 0.85rem;
        padding: 2rem 0;
        border-top: 1px solid #dee2e6;
        margin-top: 2rem;
    }

    /* Amélioration des boutons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    """Point d'entrée principal de l'application"""

    # Sidebar
    with st.sidebar:
        # Logo
        logo_path = Path(__file__).parent / "logo-removebg-preview.png"
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1 style="color: #0066cc; margin: 0;">🏥</h1>
                <h2 style="color: #0066cc; margin: 0;">RedFlag-AI</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        st.markdown("### 🧭 Navigation")

        mode = st.radio(
            "Choisir un mode",
            options=[
                "🎬 Simulation",
                "💬 Interactif",
                "📊 Métriques & Écologie",
                "📚 Base de Connaissances",
                "✅ Validation Infirmière",
                "⚙️ Gestion Modèles"
            ],
            index=0,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Informations système
        st.markdown("### ℹ️ À propos")

        st.info("""
        **RedFlag-AI v2.0**

        🎯 **Grille FRENCH** (SFMU)
        🤖 **ML:** XGBoost
        📖 **RAG:** FAISS + MiniLM
        📈 **Tracking:** MLflow
        """)

        st.markdown("---")

        # Métriques écologiques rapides
        st.markdown("### 🌱 Impact Écologique")
        with st.expander("Voir les stats", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tokens/triage", "~500", help="Estimation moyenne")
            with col2:
                st.metric("CO2/triage", "~0.2g", help="Estimation GPU")

            st.caption("*Estimations modèle local*")

        st.markdown("---")

        # Footer sidebar
        st.markdown("""
        <div style="text-align: center; font-size: 0.8rem; color: #6c757d;">
            <strong>🎓 M2 SISE - 2025</strong><br>
            Projet Data for Good<br>
            <em>Sujet 1 : Agent de Triage</em>
        </div>
        """, unsafe_allow_html=True)

    # Header principal
    st.markdown('<h1 class="main-header">🏥 RedFlag-AI</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Système Intelligent d\'Aide au Triage des Urgences</p>',
        unsafe_allow_html=True
    )

    # Barre d'état rapide
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        st.markdown("""
        <div class="status-badge status-ok">🟢 ML Model</div>
        """, unsafe_allow_html=True)

    with status_col2:
        st.markdown("""
        <div class="status-badge status-ok">🟢 RAG Engine</div>
        """, unsafe_allow_html=True)

    with status_col3:
        st.markdown("""
        <div class="status-badge status-warning">🟡 API Backend</div>
        """, unsafe_allow_html=True)

    with status_col4:
        st.markdown("""
        <div class="status-badge status-ok">🟢 FRENCH Grid</div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Contenu principal selon le mode
    if "Simulation" in mode:
        render_simulation_mode()
    elif "Interactif" in mode:
        render_interactive_mode()
    elif "Métriques" in mode:
        render_metrics_dashboard()
    elif "Base de Connaissances" in mode:
        render_knowledge_base()
    elif "Validation" in mode:
        render_validation_mode()
    elif "Modèles" in mode:
        render_models_management()
    else:
        render_simulation_mode()

    # Footer
    st.markdown("""
    <div class="footer">
        <p>
            ⚕️ <strong>RedFlag-AI</strong> - Projet Académique<br>
            <span style="color: #dc3545;">⚠️ Ne pas utiliser en production clinique</span><br>
            <small>Développé avec ❤️ pour Data for Good</small>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
