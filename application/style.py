import streamlit as st

def apply_style():
    """Applique le style CSS commun à toutes les pages."""
    st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

        /* Appliquer la police partout */
        html, body, [class*="st-"] {
            font-family: 'Roboto', sans-serif;
        }

        /* Sidebar verte */
        section[data-testid="stSidebar"] {
            background-color: #BED3C3;
        }

        /* Cacher le lien "app" dans la sidebar (premier élément de la nav) */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > ul > li:first-child {
            display: none;
        }

        /* Titre dans la sidebar */
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            background-color: #BED3C3;
            padding: 20px;
        }

        /* Liens de navigation */
        section[data-testid="stSidebar"] a span {
            color: black !important;
        }

        section[data-testid="stSidebar"] a {
            background-color: white;
            border-radius: 5px;
            margin: 5px 10px;
            padding: 10px;
        }

        section[data-testid="stSidebar"] a:hover {
            background-color: #f0f0f0;
        }

        /* Contenu principal pleine largeur */
        .main .block-container {
            max-width: 100%;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Header avec titre */
        .header-bar {
            background-color: #BED3C3 ;
            padding: 20px 30px;
            margin: -1rem -2rem 1rem -2rem;
            text-align: right;
        }

        .header-bar h2 {
            color: #ffffff ;
            margin: 0;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # Affiche le titre dans le header
    st.markdown('<div class="header-bar"><h2>Triage urgences</h2></div>', unsafe_allow_html=True)
