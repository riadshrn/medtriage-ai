import streamlit as st

def apply_style():
    """Applique le style CSS commun a toutes les pages."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

        html, body, p, h1, h2, h3, h4, h5, h6, span, div, label, button, input, textarea {
            font-family: 'Roboto', sans-serif;
        }

        section[data-testid="stSidebar"] {
            background-color: #BED3C3;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > ul > li:first-child {
            display: none;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            background-color: #BED3C3;
            padding: 20px;
        }

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

        .main .block-container {
            max-width: 100%;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        .header-bar {
            background-color: #BED3C3;
            padding: 20px 30px;
            margin: -1rem -2rem 1rem -2rem;
            text-align: right;
        }

        .header-bar h2 {
            color: #ffffff;
            margin: 0;
            font-weight: bold;
        }
        
        .triage-badge {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-weight: bold;
            font-size: 1.2rem;
            color: white !important; /* Force le texte en blanc */
            text-transform: uppercase;
            letter-spacing: 1px;
            display: block; /* Assure que le div prend la largeur */
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header-bar"><h2>MedTriage-AI</h2></div>', unsafe_allow_html=True)
