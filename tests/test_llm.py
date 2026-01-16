"""
Tests unitaires pour le module LLM.
"""

import pytest
import numpy as np
from pathlib import Path

from src.llm import EmbeddingGenerator, VectorStore, PromptTemplates


class TestEmbeddingGenerator:
    """Tests pour EmbeddingGenerator."""

    def test_init(self):
        """Test de l'initialisation."""
        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        assert generator.embedding_dim == 384  # Dimension de ce modèle

    def test_encode_single_text(self):
        """Test d'encodage d'un seul texte."""
        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        text = "Patient avec fièvre élevée"

        embedding = generator.encode(text)

        assert embedding.shape == (1, 384)
        assert np.all(np.isfinite(embedding))

    def test_encode_multiple_texts(self):
        """Test d'encodage de plusieurs textes."""
        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        texts = ["Urgence vitale", "Douleur thoracique", "Fièvre modérée"]

        embeddings = generator.encode(texts)

        assert embeddings.shape == (3, 384)
        assert np.all(np.isfinite(embeddings))

    def test_similarity(self):
        """Test de calcul de similarité."""
        generator = EmbeddingGenerator("all-MiniLM-L6-v2")

        # Test avec le même texte (doit donner une similarité très élevée)
        sim_identical = generator.similarity("fièvre élevée", "fièvre élevée")

        # Textes différents
        sim_different = generator.similarity("fièvre élevée", "patient stable")

        # La similarité doit être entre 0 et 1
        assert 0 <= sim_identical <= 1
        assert 0 <= sim_different <= 1

        # Un texte identique doit avoir une similarité proche de 1
        assert sim_identical > 0.99

        # Des textes différents ont une similarité plus faible
        assert sim_different < sim_identical


class TestVectorStore:
    """Tests pour VectorStore."""

    def test_init(self):
        """Test de l'initialisation."""
        store = VectorStore(embedding_dim=384)
        assert store.embedding_dim == 384
        assert len(store.documents) == 0

    def test_add_and_search(self):
        """Test d'ajout et de recherche."""
        store = VectorStore(embedding_dim=384)

        # Documents de test
        documents = [
            "Urgence vitale avec détresse respiratoire",
            "Fièvre élevée sans signe de gravité",
            "Douleur légère",
        ]

        # Embeddings factices (normalisés)
        embeddings = np.random.rand(3, 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Ajout
        store.add_documents(documents, embeddings)

        assert len(store.documents) == 3

        # Recherche
        query_emb = embeddings[0:1]  # Même embedding que le premier document
        results = store.search(query_emb, top_k=2)

        assert len(results) == 2
        assert results[0][0] == documents[0]  # Premier résultat = premier document

    def test_save_and_load(self, tmp_path):
        """Test de sauvegarde et chargement."""
        store = VectorStore(embedding_dim=384)

        # Ajout de documents
        documents = ["Doc 1", "Doc 2"]
        embeddings = np.random.rand(2, 384).astype(np.float32)
        store.add_documents(documents, embeddings)

        # Sauvegarde
        store_path = tmp_path / "test_store"
        store.save(str(store_path))

        # Vérification des fichiers
        assert Path(str(store_path) + ".faiss").exists()
        assert Path(str(store_path) + ".pkl").exists()

        # Chargement
        loaded_store = VectorStore.load(str(store_path))

        assert loaded_store.embedding_dim == 384
        assert len(loaded_store.documents) == 2
        assert loaded_store.documents[0] == "Doc 1"

    def test_get_stats(self):
        """Test des statistiques."""
        store = VectorStore(embedding_dim=384)

        documents = ["Doc 1", "Doc 2", "Doc 3"]
        embeddings = np.random.rand(3, 384).astype(np.float32)
        store.add_documents(documents, embeddings)

        stats = store.get_stats()

        assert stats["n_documents"] == 3
        assert stats["embedding_dim"] == 384
        assert stats["index_size"] == 3


class TestPromptTemplates:
    """Tests pour PromptTemplates."""

    def test_format_justification_prompt(self):
        """Test de formatage du prompt de justification."""
        patient_data = {
            "age": 45,
            "sexe": "M",
            "motif_consultation": "Douleur thoracique",
            "constantes": {
                "frequence_cardiaque": 120,
                "pression_systolique": 140,
                "pression_diastolique": 90,
                "frequence_respiratoire": 22,
                "temperature": 37.5,
                "saturation_oxygene": 92,
                "echelle_douleur": 7,
            },
        }

        prompt = PromptTemplates.format_justification_prompt(
            patient_data=patient_data,
            gravity_level="JAUNE",
            confidence=0.85,
            medical_context="Contexte médical test",
        )

        # Vérifications
        assert "45 ans" in prompt
        assert "Douleur thoracique" in prompt
        assert "JAUNE" in prompt
        assert "120 bpm" in prompt
        assert "92%" in prompt
        assert "Contexte médical test" in prompt

    def test_format_simple_prompt(self):
        """Test de formatage du prompt simplifié."""
        patient_data = {
            "age": 70,
            "sexe": "F",
            "motif_consultation": "Fièvre",
            "constantes": {
                "frequence_cardiaque": 95,
                "temperature": 39.2,
                "saturation_oxygene": 96,
            },
        }

        prompt = PromptTemplates.format_simple_prompt(
            patient_data=patient_data,
            gravity_level="JAUNE",
            medical_context="Test",
        )

        assert "70 ans" in prompt
        assert "Fièvre" in prompt
        assert "JAUNE" in prompt
        assert "95" in prompt  # FC
        assert "39.2" in prompt  # Température
