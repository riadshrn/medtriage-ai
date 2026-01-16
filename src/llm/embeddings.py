"""
Génération d'embeddings pour le système RAG.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    Génère des embeddings vectoriels à partir de texte.

    Utilise sentence-transformers (Hugging Face) pour créer des représentations
    vectorielles denses du texte médical.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialise le générateur d'embeddings.

        Args:
            model_name: Nom du modèle sentence-transformers
                       (défaut: all-MiniLM-L6-v2, léger et performant)
        """
        self.model_name = model_name
        print(f"Chargement du modele d'embeddings : {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Dimension des embeddings : {self.embedding_dim}")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Génère des embeddings pour un ou plusieurs textes.

        Args:
            texts: Texte(s) à encoder
            batch_size: Taille des batchs pour l'encodage
            show_progress: Afficher la barre de progression

        Returns:
            np.ndarray: Embeddings (shape: [n_texts, embedding_dim])
        """
        # Conversion en liste si texte unique
        if isinstance(texts, str):
            texts = [texts]

        # Génération des embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        return embeddings

    def encode_documents(
        self, documents: List[str], show_progress: bool = True
    ) -> np.ndarray:
        """
        Encode une liste de documents médicaux.

        Args:
            documents: Liste de documents à encoder
            show_progress: Afficher la progression

        Returns:
            np.ndarray: Embeddings des documents
        """
        print(f"Encodage de {len(documents)} documents...")
        embeddings = self.encode(documents, show_progress=show_progress)
        print(f"Embeddings generes : {embeddings.shape}")
        return embeddings

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité cosinus entre deux textes.

        Args:
            text1: Premier texte
            text2: Deuxième texte

        Returns:
            float: Similarité cosinus (0-1)
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)

        # Similarité cosinus
        similarity = np.dot(emb1[0], emb2[0]) / (
            np.linalg.norm(emb1[0]) * np.linalg.norm(emb2[0])
        )

        return float(similarity)
