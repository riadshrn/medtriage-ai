"""
Script de construction de la base de connaissances vectorielle.

Usage:
    python scripts/build_knowledge_base.py --input docs/medical_knowledge.md --output data/vector_store/medical_kb
"""

import argparse
import sys
from pathlib import Path
import re

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm import EmbeddingGenerator, VectorStore


def parse_medical_knowledge(md_file: str) -> list:
    """
    Parse le fichier Markdown de connaissances médicales.

    Args:
        md_file: Chemin vers le fichier Markdown

    Returns:
        list: Liste de tuples (titre, contenu, metadata)
    """
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Découpage par sections principales (## ou ###)
    sections = []
    current_section = {"title": "", "content": [], "level": 0}

    for line in content.split("\n"):
        # Détection des titres
        if line.startswith("###"):
            # Sauvegarde de la section précédente
            if current_section["content"]:
                sections.append(current_section)

            # Nouvelle section niveau 3
            title = line.replace("###", "").strip()
            current_section = {"title": title, "content": [], "level": 3}

        elif line.startswith("##"):
            # Sauvegarde de la section précédente
            if current_section["content"]:
                sections.append(current_section)

            # Nouvelle section niveau 2
            title = line.replace("##", "").strip()
            current_section = {"title": title, "content": [], "level": 2}

        elif line.startswith("#"):
            # Titre principal (niveau 1), on ignore
            continue

        else:
            # Ajout du contenu
            if line.strip():
                current_section["content"].append(line)

    # Ajout de la dernière section
    if current_section["content"]:
        sections.append(current_section)

    # Formatage des documents
    documents = []
    for section in sections:
        if not section["content"]:
            continue

        # Titre
        title = section["title"]

        # Contenu
        content = "\n".join(section["content"]).strip()

        # Document complet
        doc_text = f"{title}\n\n{content}"

        # Métadonnées
        metadata = {
            "title": title,
            "level": section["level"],
            "length": len(content),
        }

        documents.append((doc_text, metadata))

    return documents


def main():
    parser = argparse.ArgumentParser(
        description="Construit la base de connaissances vectorielle"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="docs/medical_knowledge.md",
        help="Fichier Markdown de connaissances (defaut: docs/medical_knowledge.md)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/vector_store/medical_kb",
        help="Chemin de sortie du vector store (defaut: data/vector_store/medical_kb)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Modele d'embeddings (defaut: all-MiniLM-L6-v2)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CONSTRUCTION DE LA BASE DE CONNAISSANCES")
    print("=" * 60)

    # Vérification de l'existence du fichier
    if not Path(args.input).exists():
        print(f"Erreur : Le fichier {args.input} n'existe pas.")
        sys.exit(1)

    # Parsing du fichier Markdown
    print(f"\nParsing du fichier : {args.input}")
    documents_data = parse_medical_knowledge(args.input)
    print(f"  {len(documents_data)} sections trouvees")

    # Extraction des textes et métadonnées
    documents = [doc[0] for doc in documents_data]
    metadata_list = [doc[1] for doc in documents_data]

    # Affichage des premières sections
    print("\nPremières sections :")
    for i, (doc, meta) in enumerate(documents_data[:3], 1):
        print(f"  [{i}] {meta['title']} ({meta['length']} caracteres)")

    # Génération des embeddings
    print(f"\nGeneration des embeddings avec {args.embedding_model}...")
    embedding_generator = EmbeddingGenerator(args.embedding_model)
    embeddings = embedding_generator.encode_documents(documents, show_progress=True)

    # Création du vector store
    print("\nCreation du vector store...")
    vector_store = VectorStore(embedding_dim=embedding_generator.embedding_dim)
    vector_store.add_documents(documents, embeddings, metadata_list)

    # Sauvegarde
    print(f"\nSauvegarde du vector store : {args.output}")
    vector_store.save(args.output)

    # Statistiques
    stats = vector_store.get_stats()
    print("\nStatistiques :")
    print(f"  Documents      : {stats['n_documents']}")
    print(f"  Dimension      : {stats['embedding_dim']}")
    print(f"  Taille index   : {stats['index_size']}")

    # Test de recherche
    print("\n" + "=" * 60)
    print("TEST DE RECHERCHE")
    print("=" * 60)

    test_queries = [
        "urgence vitale saturation oxygene",
        "fievre elevee temperature",
        "douleur thoracique",
    ]

    for query in test_queries:
        print(f"\nRequete : '{query}'")
        query_emb = embedding_generator.encode(query)
        results = vector_store.search(query_emb, top_k=2)

        for i, (doc, score, meta) in enumerate(results, 1):
            print(f"  [{i}] Score: {score:.3f} | {meta['title']}")
            print(f"      {doc[:100]}...")

    print("\n" + "=" * 60)
    print("BASE DE CONNAISSANCES CONSTRUITE AVEC SUCCES")
    print("=" * 60)


if __name__ == "__main__":
    main()
