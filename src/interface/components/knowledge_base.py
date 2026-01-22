"""
Visualisation de la Base de Connaissances (FAISS + Documents Médicaux)
Permet d'explorer les données utilisées par le RAG
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import pickle

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Imports conditionnels
try:
    from src.llm.vector_store import VectorStore
    from src.llm.embeddings import EmbeddingModel
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False


def render_knowledge_base():
    """Rendu de la page de visualisation de la base de connaissances"""

    st.header("📚 Base de Connaissances Médicale")
    st.markdown("""
    Cette page permet d'explorer la **base documentaire** utilisée par le système RAG
    pour enrichir les justifications de triage.
    """)

    # Tabs pour les différentes vues
    tab1, tab2, tab3 = st.tabs([
        "📊 Vue d'ensemble",
        "🔍 Recherche Sémantique",
        "📄 Documents"
    ])

    with tab1:
        render_overview()

    with tab2:
        render_semantic_search()

    with tab3:
        render_documents_list()


def render_overview():
    """Vue d'ensemble de la base de connaissances"""

    st.subheader("Statistiques de la Base")

    # Charger le vector store
    vector_store_path = Path("data/vector_store/medical_kb")

    if not vector_store_path.with_suffix(".pkl").exists():
        st.warning("⚠️ Base de connaissances non trouvée. Lancez d'abord le script de construction.")
        st.code("python scripts/build_knowledge_base.py", language="bash")

        # Afficher des stats par défaut
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents", "0")
        with col2:
            st.metric("Dimension Embeddings", "384")
        with col3:
            st.metric("Modèle", "all-MiniLM-L6-v2")
        with col4:
            st.metric("Index", "FAISS (L2)")
        return

    try:
        # Charger les données
        with open(str(vector_store_path) + ".pkl", "rb") as f:
            data = pickle.load(f)

        n_docs = len(data.get("documents", []))
        embedding_dim = data.get("embedding_dim", 384)
        metadata_list = data.get("metadata", [])

        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📄 Documents", n_docs)
        with col2:
            st.metric("📐 Dimension", embedding_dim)
        with col3:
            st.metric("🤖 Modèle", "MiniLM-L6")
        with col4:
            st.metric("⚡ Index", "FAISS")

        st.markdown("---")

        # Distribution par catégorie
        st.subheader("📊 Distribution par Catégorie")

        if metadata_list:
            categories = {}
            for meta in metadata_list:
                cat = meta.get("category", "Non classé")
                categories[cat] = categories.get(cat, 0) + 1

            if categories:
                df_cat = pd.DataFrame({
                    "Catégorie": list(categories.keys()),
                    "Nombre": list(categories.values())
                })
                st.bar_chart(df_cat.set_index("Catégorie"))

        # Informations sur le stockage
        st.markdown("---")
        st.subheader("💾 Stockage")

        faiss_file = vector_store_path.with_suffix(".faiss")
        pkl_file = vector_store_path.with_suffix(".pkl")

        col1, col2 = st.columns(2)
        with col1:
            if faiss_file.exists():
                size_mb = faiss_file.stat().st_size / (1024 * 1024)
                st.metric("Index FAISS", f"{size_mb:.2f} MB")
        with col2:
            if pkl_file.exists():
                size_mb = pkl_file.stat().st_size / (1024 * 1024)
                st.metric("Métadonnées", f"{size_mb:.2f} MB")

    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")


def render_semantic_search():
    """Interface de recherche sémantique"""

    st.subheader("🔍 Test de Recherche Sémantique")
    st.markdown("""
    Testez la recherche dans la base de connaissances.
    Le système trouve les documents les plus pertinents pour une requête.
    """)

    # Requêtes prédéfinies
    predefined_queries = [
        "Douleur thoracique avec irradiation bras gauche",
        "Détresse respiratoire aiguë",
        "Traumatisme crânien avec perte de conscience",
        "Réaction allergique sévère",
        "Hypotension et tachycardie",
        "Fièvre élevée chez l'enfant"
    ]

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Requête de recherche",
            placeholder="Ex: douleur thoracique avec essoufflement..."
        )

    with col2:
        selected_preset = st.selectbox(
            "Requêtes prédéfinies",
            options=["-- Choisir --"] + predefined_queries
        )

    if selected_preset != "-- Choisir --":
        query = selected_preset

    top_k = st.slider("Nombre de résultats", 1, 10, 3)

    if st.button("🔍 Rechercher", type="primary") and query:
        vector_store_path = Path("data/vector_store/medical_kb")

        if not vector_store_path.with_suffix(".pkl").exists():
            st.error("Base de connaissances non disponible")
            return

        try:
            with st.spinner("Recherche en cours..."):
                # Charger le vector store
                if VECTOR_STORE_AVAILABLE:
                    vs = VectorStore.load(str(vector_store_path))
                    embedder = EmbeddingModel()

                    # Générer l'embedding de la requête
                    query_embedding = embedder.embed([query])

                    # Rechercher
                    results = vs.search(query_embedding, top_k=top_k)

                    # Afficher les résultats
                    st.markdown("### Résultats")

                    for i, (doc, score, meta) in enumerate(results, 1):
                        with st.expander(f"**#{i}** - Score: {score:.3f} - {meta.get('category', 'N/A')}"):
                            st.markdown(doc)
                            if meta:
                                st.json(meta)
                else:
                    st.error("Module vector_store non disponible")

        except Exception as e:
            st.error(f"Erreur de recherche: {e}")


def render_documents_list():
    """Liste paginée des documents"""

    st.subheader("📄 Exploration des Documents")

    vector_store_path = Path("data/vector_store/medical_kb")

    if not vector_store_path.with_suffix(".pkl").exists():
        st.warning("Base de connaissances non disponible")
        return

    try:
        with open(str(vector_store_path) + ".pkl", "rb") as f:
            data = pickle.load(f)

        documents = data.get("documents", [])
        metadata_list = data.get("metadata", [])

        if not documents:
            st.info("Aucun document dans la base")
            return

        # Filtres
        col1, col2 = st.columns(2)

        with col1:
            # Extraire les catégories uniques
            categories = list(set(m.get("category", "Non classé") for m in metadata_list))
            filter_cat = st.multiselect(
                "Filtrer par catégorie",
                options=categories,
                default=[]
            )

        with col2:
            search_text = st.text_input("Recherche textuelle", placeholder="Mot-clé...")

        # Filtrage
        filtered_docs = []
        for i, (doc, meta) in enumerate(zip(documents, metadata_list)):
            cat = meta.get("category", "Non classé")

            # Appliquer filtres
            if filter_cat and cat not in filter_cat:
                continue
            if search_text and search_text.lower() not in doc.lower():
                continue

            filtered_docs.append((i, doc, meta))

        st.info(f"📊 {len(filtered_docs)} documents affichés sur {len(documents)}")

        # Pagination
        docs_per_page = 10
        total_pages = max(1, (len(filtered_docs) + docs_per_page - 1) // docs_per_page)

        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

        start_idx = (page - 1) * docs_per_page
        end_idx = start_idx + docs_per_page

        for idx, doc, meta in filtered_docs[start_idx:end_idx]:
            with st.expander(f"Document #{idx + 1} - {meta.get('category', 'N/A')}"):
                st.markdown(doc[:500] + "..." if len(doc) > 500 else doc)

                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"**Catégorie:** {meta.get('category', 'N/A')}")
                with col2:
                    st.caption(f"**Longueur:** {len(doc)} caractères")

        # Navigation
        st.markdown(f"Page {page} / {total_pages}")

    except Exception as e:
        st.error(f"Erreur: {e}")
