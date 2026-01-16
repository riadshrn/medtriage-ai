"""
Store vectoriel pour la recherche sémantique.
"""

import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss


class VectorStore:
    """
    Store vectoriel utilisant FAISS pour la recherche rapide de similarité.

    Permet de stocker des embeddings et de retrouver les documents
    les plus similaires à une requête.
    """

    def __init__(self, embedding_dim: int):
        """
        Initialise le vector store.

        Args:
            embedding_dim: Dimension des embeddings
        """
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)  # Index L2 (distance euclidienne)
        self.documents: List[str] = []
        self.metadata: List[dict] = []

    def add_documents(
        self,
        documents: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[dict]] = None,
    ) -> None:
        """
        Ajoute des documents au store avec leurs embeddings.

        Args:
            documents: Liste des documents textuels
            embeddings: Embeddings correspondants
            metadata: Métadonnées optionnelles pour chaque document
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Nombre de documents ({len(documents)}) != nombre d'embeddings ({len(embeddings)})"
            )

        # Normalisation des embeddings pour la similarité cosinus
        faiss.normalize_L2(embeddings)

        # Ajout à l'index FAISS
        self.index.add(embeddings)

        # Sauvegarde des documents
        self.documents.extend(documents)

        # Sauvegarde des métadonnées
        if metadata is None:
            metadata = [{}] * len(documents)
        self.metadata.extend(metadata)

        print(f"{len(documents)} documents ajoutes au vector store")
        print(f"Total : {len(self.documents)} documents")

    def search(
        self, query_embedding: np.ndarray, top_k: int = 3
    ) -> List[Tuple[str, float, dict]]:
        """
        Recherche les documents les plus similaires à une requête.

        Args:
            query_embedding: Embedding de la requête
            top_k: Nombre de résultats à retourner

        Returns:
            List[Tuple[document, score, metadata]]:
                Liste des documents les plus similaires avec leur score
        """
        if len(self.documents) == 0:
            return []

        # Normalisation pour similarité cosinus
        faiss.normalize_L2(query_embedding)

        # Recherche dans l'index
        distances, indices = self.index.search(query_embedding, top_k)

        # Construction des résultats
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):  # Vérification de validité
                document = self.documents[idx]
                # Conversion distance L2 → similarité cosinus approximative
                similarity = 1.0 / (1.0 + distances[0][i])
                metadata = self.metadata[idx]
                results.append((document, similarity, metadata))

        return results

    def save(self, store_path: str) -> None:
        """
        Sauvegarde le vector store sur disque.

        Args:
            store_path: Chemin de sauvegarde (sans extension)
        """
        store_path = Path(store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarde de l'index FAISS
        faiss.write_index(self.index, str(store_path) + ".faiss")

        # Sauvegarde des documents et métadonnées
        with open(str(store_path) + ".pkl", "wb") as f:
            pickle.dump(
                {
                    "documents": self.documents,
                    "metadata": self.metadata,
                    "embedding_dim": self.embedding_dim,
                },
                f,
            )

        print(f"Vector store sauvegarde : {store_path}")

    @classmethod
    def load(cls, store_path: str) -> "VectorStore":
        """
        Charge un vector store depuis le disque.

        Args:
            store_path: Chemin du store (sans extension)

        Returns:
            VectorStore: Instance chargée
        """
        store_path = Path(store_path)

        # Chargement de l'index FAISS
        index = faiss.read_index(str(store_path) + ".faiss")

        # Chargement des documents et métadonnées
        with open(str(store_path) + ".pkl", "rb") as f:
            data = pickle.load(f)

        # Reconstruction du vector store
        vector_store = cls(embedding_dim=data["embedding_dim"])
        vector_store.index = index
        vector_store.documents = data["documents"]
        vector_store.metadata = data["metadata"]

        print(f"Vector store charge : {store_path}")
        print(f"  {len(vector_store.documents)} documents")

        return vector_store

    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur le vector store.

        Returns:
            dict: Statistiques
        """
        return {
            "n_documents": len(self.documents),
            "embedding_dim": self.embedding_dim,
            "index_size": self.index.ntotal,
        }
