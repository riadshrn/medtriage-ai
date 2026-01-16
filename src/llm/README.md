# Module RAG et LLM

Ce module implemente le systeme RAG (Retrieval-Augmented Generation) pour generer des justifications medicales.

## Architecture

```
src/llm/
├── __init__.py
├── embeddings.py      # Generateur d'embeddings
├── vector_store.py    # Base vectorielle FAISS
├── rag_engine.py      # Moteur RAG complet
└── prompts.py         # Templates de prompts
```

## Classes

### EmbeddingGenerator

Genere des embeddings avec sentence-transformers.

**Modele** : `all-MiniLM-L6-v2`
- Dimension : 384
- Rapide et leger
- Bon pour la similarite semantique

**Methodes :**
- `encode(texts)` : Encode une liste de textes
- `similarity(text1, text2)` : Calcule la similarite cosinus

### VectorStore

Base de donnees vectorielle avec FAISS.

**Methodes :**
- `add_documents(texts, metadatas)` : Ajoute des documents
- `search(query, k)` : Recherche les k plus proches
- `save(path)` / `load(path)` : Persistence
- `get_stats()` : Statistiques du store

### RAGEngine

Moteur RAG complet combinant recherche et generation.

**Pipeline :**
1. Encode la requete en embedding
2. Recherche les documents pertinents dans le vector store
3. Construit le contexte avec les documents trouves
4. Genere la reponse avec le LLM (ou fallback)

**Modele LLM** : `facebook/opt-350m` (optionnel, fallback si non disponible)

### PromptTemplates

Templates de prompts pour la generation de justifications.

## Tests

```bash
python -m pytest tests/test_llm.py -v
```

### Resultats des tests

| Test | Description | Statut |
|------|-------------|--------|
| test_init | Initialisation EmbeddingGenerator | PASSED |
| test_encode_single_text | Encodage d'un texte | PASSED |
| test_encode_multiple_texts | Encodage de plusieurs textes | PASSED |
| test_similarity | Calcul de similarite | PASSED |
| test_init (VectorStore) | Initialisation VectorStore | PASSED |
| test_add_and_search | Ajout et recherche | PASSED |
| test_save_and_load | Sauvegarde et chargement | PASSED |
| test_get_stats | Statistiques du store | PASSED |
| test_format_justification_prompt | Formatage prompt justification | PASSED |
| test_format_simple_prompt | Formatage prompt simple | PASSED |

**Total : 10 tests - 10 passed**

## Utilisation

```python
from src.llm import EmbeddingGenerator, VectorStore, RAGEngine

# Generer des embeddings
embedder = EmbeddingGenerator()
embeddings = embedder.encode(["Douleur thoracique", "Dyspnee"])

# Creer un vector store
store = VectorStore(embedding_dim=384)
store.add_documents(
    texts=["Tachycardie : FC > 100 bpm", "Bradycardie : FC < 60 bpm"],
    metadatas=[{"topic": "cardio"}, {"topic": "cardio"}]
)

# Rechercher
results = store.search("frequence cardiaque elevee", k=2)

# RAG complet
rag = RAGEngine(vector_store=store, embedder=embedder)
justification = rag.generate_justification(
    patient=patient,
    gravity=GravityLevel.JAUNE,
    red_flags=["Tachycardie"]
)
```

## Script CLI

```bash
python scripts/build_knowledge_base.py --input docs/medical_knowledge.md --output data/vector_store/medical_kb
```

## Base de connaissances

Le fichier `docs/medical_knowledge.md` contient 14 sections :
1. Classification des urgences
2. Constantes vitales normales
3. Signes de gravite cardiovasculaire
4. Signes de gravite respiratoire
5. Signes de gravite neurologique
6. Traumatologie
7. Pediatrie
8. Geriatrie
9. Obstetrique
10. Psychiatrie
11. Intoxications
12. Brulures
13. Allergies et anaphylaxie
14. Sepsis et infections severes
