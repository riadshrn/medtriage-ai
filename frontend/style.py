"""
Style CSS moderne pour MedTriage-AI.

Design professionnel pour application médicale avec:
- Palette de couleurs apaisante (bleu médical)
- Typographie claire et lisible
- Composants modernes avec ombres et transitions
- Design responsive et accessible
"""

import streamlit as st


def configure_page(page_title: str = "MedTriage-AI", page_icon: str = "🏥"):
    """
    Configure la page Streamlit avec les paramètres par défaut.
    DOIT être appelée en PREMIER dans chaque page.
    
    Args:
        page_title: Titre de la page
        page_icon: Icône de la page
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide", 
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/votre-repo',
            'Report a bug': 'https://github.com/votre-repo/issues',
            'About': "# MedTriage-AI\nAssistance intelligente au triage des urgences"
        }
    )

def apply_style():
    """Applique le style CSS moderne à toutes les pages."""

    # Configuration de la page
    st.markdown("""
    <style>
        /* ============================================
           IMPORTS & VARIABLES
           ============================================ */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            /* Couleurs principales - Palette médicale professionnelle */
            --primary-color: #0066CC;
            --primary-dark: #004999;
            --primary-light: #E6F0FF;

            /* Couleurs de triage */
            --triage-rouge: #DC2626;
            --triage-rouge-bg: #FEE2E2;
            --triage-jaune: #F59E0B;
            --triage-jaune-bg: #FEF3C7;
            --triage-vert: #10B981;
            --triage-vert-bg: #D1FAE5;
            --triage-gris: #6B7280;
            --triage-gris-bg: #F3F4F6;

            /* Neutres */
            --bg-primary: #F8FAFC;
            --bg-secondary: #FFFFFF;
            --bg-sidebar: #0F172A;
            --text-primary: #1E293B;
            --text-secondary: #64748B;
            --text-muted: #94A3B8;
            --border-color: #E2E8F0;

            /* Ombres */
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

            /* Transitions */
            --transition-fast: 150ms ease;
            --transition-normal: 250ms ease;

            /* Border radius */
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
        }

        /* ============================================
           BASE STYLES
           ============================================ */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-primary);
        }

        .main {
            background-color: var(--bg-primary);
        }

        .main .block-container {
            max-width: 100%;
            padding: 1rem 2rem;
        }

        /* ============================================
           SIDEBAR - Design moderne sombre
           ============================================ */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        /* Logo/Header dans sidebar */
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            background: transparent;
            padding: 1.5rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1rem;
        }

        /* Style des liens de navigation */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-md);
            margin: 4px 12px;
            padding: 12px 16px;
            transition: all var(--transition-normal);
            border: 1px solid transparent;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateX(4px);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 4px 12px rgba(0, 102, 204, 0.4);
        }

        section[data-testid="stSidebar"] a span {
            color: rgba(255, 255, 255, 0.9) !important;
            font-weight: 500;
            font-size: 0.95rem;
        }

        /* Texte dans la sidebar */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown {
            color: rgba(255, 255, 255, 0.85) !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: white !important;
            font-weight: 600;
        }

        /* Boutons dans sidebar */
        section[data-testid="stSidebar"] button {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            transition: all var(--transition-normal);
        }

        section[data-testid="stSidebar"] button:hover {
            background: rgba(255, 255, 255, 0.2) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
        }

        /* ============================================
           HEADER
           ============================================ */
        .app-header {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            padding: 1.5rem 2rem;
            margin: -1rem -2rem 2rem -2rem;
            border-radius: 0 0 var(--radius-xl) var(--radius-xl);
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .app-header h1 {
            color: white !important;
            margin: 0 !important;
            font-weight: 700;
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-header .subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            margin-top: 4px;
        }

        /* ============================================
           TITRES ET TYPOGRAPHIE
           ============================================ */
        h1 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
            margin-bottom: 0.5rem !important;
        }

        h2 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 1.5rem !important;
            margin-top: 1.5rem !important;
        }

        h3 {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }

        .stCaption {
            color: var(--text-muted) !important;
            font-size: 0.9rem !important;
        }

        /* ============================================
           CARTES ET CONTENEURS
           ============================================ */
        .card {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all var(--transition-normal);
        }

        .card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .card-selected {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background: var(--bg-secondary) !important;
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--border-color) !important;
            font-weight: 500 !important;
            transition: all var(--transition-normal) !important;
        }

        .streamlit-expanderHeader:hover {
            background: var(--bg-primary) !important;
            border-color: var(--primary-color) !important;
        }

        .streamlit-expanderContent {
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border-color) !important;
            border-top: none !important;
            border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
        }

        /* ============================================
           BOUTONS
           ============================================ */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: white !important;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-sm);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            filter: brightness(1.1);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Bouton secondaire */
        .stButton > button[kind="secondary"],
        div[data-testid="stButton"] button[kind="secondary"] {
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            border: 2px solid var(--border-color) !important;
        }

        .stButton > button[kind="secondary"]:hover {
            border-color: var(--primary-color) !important;
            color: var(--primary-color) !important;
        }

        /* Bouton désactivé */
        .stButton > button:disabled {
            background: var(--triage-gris-bg) !important;
            color: var(--text-muted) !important;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* ============================================
           BADGES DE TRIAGE
           ============================================ */
        .triage-badge {
            padding: 1.25rem 1.5rem;
            border-radius: var(--radius-lg);
            text-align: center;
            margin-bottom: 1.5rem;
            font-weight: 700;
            font-size: 1.3rem;
            color: white !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }

        .triage-badge::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
            pointer-events: none;
        }

        .triage-rouge {
            background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
            animation: pulse-red 2s infinite;
        }

        .triage-jaune {
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        }

        .triage-vert {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        }

        .triage-gris {
            background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
        }

        @keyframes pulse-red {
            0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
            50% { box-shadow: 0 0 0 15px rgba(220, 38, 38, 0); }
        }

        /* ============================================
           MÉTRIQUES
           ============================================ */
        [data-testid="stMetric"] {
            background: var(--bg-secondary);
            padding: 1.25rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
        }

        [data-testid="stMetric"]:hover {
            box-shadow: var(--shadow-md);
            border-color: var(--primary-light);
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        [data-testid="stMetricValue"] {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            font-size: 1.75rem !important;
        }

        /* ============================================
           INPUTS ET FORMULAIRES
           ============================================ */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            border-radius: var(--radius-md) !important;
            border: 2px solid var(--border-color) !important;
            transition: all var(--transition-normal) !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px var(--primary-light) !important;
        }

        /* ============================================
           CHAT
           ============================================ */
        .stChatMessage {
            background: var(--bg-secondary) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1rem !important;
            margin-bottom: 0.75rem !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        [data-testid="stChatMessageContent"] {
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }

        /* Chat input */
        .stChatInputContainer {
            border-radius: var(--radius-lg) !important;
            border: 2px solid var(--border-color) !important;
            background: var(--bg-secondary) !important;
            padding: 0.5rem !important;
        }

        .stChatInputContainer:focus-within {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px var(--primary-light) !important;
        }

        /* ============================================
           ALERTES ET MESSAGES
           ============================================ */
        .stAlert {
            border-radius: var(--radius-md) !important;
            border-left-width: 4px !important;
        }

        div[data-testid="stAlert"][data-baseweb="notification"] {
            background: var(--bg-secondary) !important;
        }

        /* Info */
        .element-container div[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {
            background: var(--primary-light) !important;
            border-left-color: var(--primary-color) !important;
        }

        /* Success */
        .element-container div[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {
            background: var(--triage-vert-bg) !important;
            border-left-color: var(--triage-vert) !important;
        }

        /* Warning */
        .element-container div[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {
            background: var(--triage-jaune-bg) !important;
            border-left-color: var(--triage-jaune) !important;
        }

        /* Error */
        .element-container div[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {
            background: var(--triage-rouge-bg) !important;
            border-left-color: var(--triage-rouge) !important;
        }

        /* ============================================
           TABS
           ============================================ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: var(--bg-secondary);
            padding: 8px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-md);
            padding: 10px 20px;
            font-weight: 500;
            transition: all var(--transition-normal);
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: var(--bg-primary);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
            color: white !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }

        /* ============================================
           JSON VIEWER
           ============================================ */
        .stJson {
            background: #1E293B !important;
            border-radius: var(--radius-md) !important;
            padding: 1rem !important;
            font-size: 0.85rem !important;
        }

        /* ============================================
           PROGRESS BARS
           ============================================ */
        .stProgress > div > div {
            background: var(--border-color) !important;
            border-radius: var(--radius-sm) !important;
        }

        .stProgress > div > div > div {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--triage-vert) 100%) !important;
            border-radius: var(--radius-sm) !important;
        }

        /* ============================================
           SPINNERS
           ============================================ */
        .stSpinner > div {
            border-top-color: var(--primary-color) !important;
        }

        /* ============================================
           PATIENT CARDS (Custom)
           ============================================ */
        .patient-card {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            border: 2px solid var(--border-color);
            transition: all var(--transition-normal);
            cursor: pointer;
            min-height: 140px;
        }

        .patient-card:hover {
            border-color: var(--primary-color);
            box-shadow: var(--shadow-md);
            transform: translateY(-4px);
        }

        .patient-card.selected {
            border-color: var(--primary-color);
            background: var(--primary-light);
            box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.2);
        }

        .patient-card-icon {
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 0.75rem;
        }

        .patient-card-title {
            font-weight: 600;
            font-size: 1rem;
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .patient-card-level {
            font-size: 0.85rem;
            text-align: center;
            color: var(--text-secondary);
            padding: 4px 12px;
            background: var(--bg-primary);
            border-radius: var(--radius-sm);
            display: inline-block;
        }

        /* ============================================
           DATA PANEL (Mode Interactif)
           ============================================ */
        .data-panel {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            height: 100%;
        }

        .data-panel-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }

        .data-panel-header h3 {
            margin: 0 !important;
            color: var(--text-primary) !important;
        }

        /* ============================================
           SCROLLBAR CUSTOM
           ============================================ */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--text-muted);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }

        /* ============================================
           ANIMATIONS
           ============================================ */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-fade-in {
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .animate-slide-in {
            animation: slideIn 0.4s ease-out;
        }

        /* ============================================
           RESPONSIVE
           ============================================ */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 0.5rem 1rem;
            }

            .app-header {
                margin: -0.5rem -1rem 1.5rem -1rem;
                padding: 1rem 1.5rem;
                flex-direction: column;
                text-align: center;
            }

            h1 {
                font-size: 1.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Header de l'application
    st.markdown('''
    <div class="app-header">
        <div>
            <h1>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
                MedTriage-AI
            </h1>
            <div class="subtitle">Assistance intelligente au triage des urgences</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_triage_badge(level: str, label: str = None) -> str:
    """
    Génère le HTML pour un badge de triage.

    Args:
        level: ROUGE, JAUNE, VERT ou GRIS
        label: Texte personnalisé (défaut: "TRIAGE : {level}")

    Returns:
        Code HTML du badge
    """
    level_upper = level.upper()
    css_class = f"triage-{level.lower()}"
    display_text = label or f"TRIAGE : {level_upper}"

    return f'''
    <div class="triage-badge {css_class}">
        {display_text}
    </div>
    '''


def render_stage_badge(stage: str) -> str:
    """
    Génère le HTML pour un badge de stage MLFlow.

    Args:
        stage: Production, Staging, Archived ou None

    Returns:
        Code HTML du badge
    """
    colors = {
        "Production": ("var(--triage-vert)", "white"),
        "Staging": ("var(--triage-jaune)", "white"),
        "Archived": ("var(--triage-gris)", "white"),
        "None": ("var(--bg-primary)", "var(--text-secondary)")
    }
    bg_color, text_color = colors.get(stage, colors["None"])

    return f'''
    <div style="
        background: {bg_color};
        color: {text_color};
        padding: 10px 16px;
        border-radius: var(--radius-md);
        text-align: center;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.85rem;
    ">
        {stage}
    </div>
    '''


def render_status_indicator(ready: bool, ready_text: str = "Prêt", not_ready_text: str = "Non prêt") -> str:
    """
    Génère le HTML pour un indicateur de status.

    Args:
        ready: Si le status est prêt
        ready_text: Texte à afficher si prêt
        not_ready_text: Texte à afficher si non prêt

    Returns:
        Code HTML de l'indicateur
    """
    if ready:
        return f'''
        <div style="
            background: var(--triage-vert);
            color: white;
            padding: 12px 16px;
            border-radius: var(--radius-md);
            text-align: center;
            font-weight: 600;
        ">
            {ready_text}
        </div>
        '''
    else:
        return f'''
        <div style="
            background: var(--triage-jaune);
            color: white;
            padding: 12px 16px;
            border-radius: var(--radius-md);
            text-align: center;
            font-weight: 600;
        ">
            {not_ready_text}
        </div>
        '''


def render_patient_card(icon: str, title: str, level: str, selected: bool = False) -> str:
    """
    Génère le HTML pour une carte patient.

    Args:
        icon: Emoji de l'icône
        title: Titre de la carte
        level: Niveau de triage attendu
        selected: Si la carte est sélectionnée

    Returns:
        Code HTML de la carte
    """
    selected_class = "selected" if selected else ""

    return f'''
    <div class="patient-card {selected_class}">
        <div class="patient-card-icon">{icon}</div>
        <div class="patient-card-title">{title}</div>
        <div style="text-align: center;">
            <span class="patient-card-level">{level}</span>
        </div>
    </div>
    '''
