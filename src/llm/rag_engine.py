"""
Moteur RAG (Retrieval-Augmented Generation) pour les justifications médicales.
"""

import time
from typing import Dict, Tuple, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .prompts import PromptTemplates


class RAGEngine:
    """
    Moteur RAG combinant :
    1. Retrieval : Recherche de contexte médical pertinent
    2. Generation : Génération de justification avec un LLM

    Utilise Hugging Face pour les deux composants.
    """

    def __init__(
        self,
        vector_store_path: Optional[str] = None,
        llm_model_name: str = "facebook/opt-350m",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialise le moteur RAG.

        Args:
            vector_store_path: Chemin vers le vector store (None = pas encore construit)
            llm_model_name: Nom du modèle LLM Hugging Face (défaut: OPT-350M, léger)
            embedding_model_name: Nom du modèle d'embeddings
        """
        print("=" * 60)
        print("INITIALISATION DU MOTEUR RAG")
        print("=" * 60)

        # Embedding generator
        self.embedding_generator = EmbeddingGenerator(embedding_model_name)

        # Vector store
        if vector_store_path:
            print(f"\nChargement du vector store : {vector_store_path}")
            self.vector_store = VectorStore.load(vector_store_path)
        else:
            print("\nVector store non initialise (a construire)")
            self.vector_store = None

        # LLM pour la génération
        print(f"\nChargement du modele LLM : {llm_model_name}")
        self.llm_model_name = llm_model_name

        # Utilisation de pipeline pour simplifier
        device = 0 if torch.cuda.is_available() else -1
        self.generator = pipeline(
            "text-generation",
            model=llm_model_name,
            device=device,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

        print(f"Modele LLM charge (device: {'GPU' if device == 0 else 'CPU'})")
        print("=" * 60)

    def retrieve_context(
        self, query: str, top_k: int = 3
    ) -> Tuple[str, list]:
        """
        Récupère le contexte médical pertinent pour une requête.

        Args:
            query: Requête (description du patient)
            top_k: Nombre de documents à récupérer

        Returns:
            Tuple[context, results]:
                - context: Contexte médical formaté
                - results: Liste des documents récupérés avec leurs scores
        """
        if self.vector_store is None:
            return "Aucune base de connaissances disponible.", []

        # Génération de l'embedding de la requête
        query_embedding = self.embedding_generator.encode(query)

        # Recherche dans le vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Formatage du contexte
        context_parts = []
        for i, (doc, score, metadata) in enumerate(results, 1):
            context_parts.append(f"[{i}] (score: {score:.2f})\n{doc}")

        context = "\n\n".join(context_parts)

        return context, results

    def generate_justification(
        self,
        patient_data: Dict,
        gravity_level: str,
        confidence: float,
        use_rag: bool = True,
        top_k: int = 2,
    ) -> Tuple[str, float, Optional[str]]:
        """
        Génère une justification médicale pour le triage.

        Args:
            patient_data: Données du patient
            gravity_level: Niveau de gravité prédit
            confidence: Score de confiance du modèle ML
            use_rag: Utiliser le RAG (retrieval) ou non
            top_k: Nombre de documents à récupérer

        Returns:
            Tuple[justification, latency, context]:
                - justification: Texte de justification généré
                - latency: Temps de génération (secondes)
                - context: Contexte médical utilisé (None si use_rag=False)
        """
        start_time = time.time()

        # 1. Retrieval (si activé)
        if use_rag and self.vector_store is not None:
            # Construction de la requête
            query = f"{gravity_level} {patient_data.get('motif_consultation', '')} SpO2={patient_data.get('constantes', {}).get('saturation_oxygene', '?')}%"
            context, _ = self.retrieve_context(query, top_k=top_k)
        else:
            context = "Pas de contexte médical disponible."

        # 2. Génération du prompt
        prompt = PromptTemplates.format_simple_prompt(
            patient_data, gravity_level, context
        )

        # 3. Génération avec le LLM
        try:
            outputs = self.generator(
                prompt,
                max_new_tokens=100,
                num_return_sequences=1,
                pad_token_id=self.generator.tokenizer.eos_token_id,
            )

            # Extraction de la justification
            generated_text = outputs[0]["generated_text"]

            # Nettoyage : extraction seulement de la partie après le prompt
            if "Justification médicale courte" in generated_text:
                justification = generated_text.split("Justification médicale courte")[1]
                justification = justification.split(":", 1)[-1].strip()
            else:
                justification = generated_text[len(prompt):].strip()

            # Nettoyage supplémentaire
            justification = justification.split("\n")[0]  # Première ligne seulement
            justification = justification.strip()

            # Fallback si vide
            if not justification or len(justification) < 20:
                justification = self._generate_fallback_justification(
                    patient_data, gravity_level, confidence
                )

        except Exception as e:
            print(f"Erreur lors de la generation : {e}")
            justification = self._generate_fallback_justification(
                patient_data, gravity_level, confidence
            )

        latency = time.time() - start_time

        return justification, latency, context if use_rag else None

    def _generate_fallback_justification(
        self, patient_data: Dict, gravity_level: str, confidence: float
    ) -> str:
        """
        Génère une justification basique basée sur des règles.

        Args:
            patient_data: Données du patient
            gravity_level: Niveau de gravité
            confidence: Score de confiance

        Returns:
            str: Justification générée
        """
        constantes = patient_data.get("constantes", {})
        motif = patient_data.get("motif_consultation", "symptômes présentés")

        # Identification des anomalies
        anomalies = []
        spo2 = constantes.get("saturation_oxygene", 100)
        fc = constantes.get("frequence_cardiaque", 70)
        temp = constantes.get("temperature", 37)
        douleur = constantes.get("echelle_douleur", 0)

        if spo2 < 90:
            anomalies.append(f"hypoxémie sévère (SpO2 {spo2}%)")
        elif spo2 < 94:
            anomalies.append(f"hypoxémie modérée (SpO2 {spo2}%)")

        if fc > 120:
            anomalies.append(f"tachycardie ({fc} bpm)")
        elif fc < 50:
            anomalies.append(f"bradycardie ({fc} bpm)")

        if temp > 39:
            anomalies.append(f"fièvre élevée ({temp}°C)")
        elif temp < 36:
            anomalies.append(f"hypothermie ({temp}°C)")

        if douleur >= 7:
            anomalies.append(f"douleur intense ({douleur}/10)")

        # Construction de la justification
        if gravity_level == "ROUGE":
            if anomalies:
                return f"Patient en urgence vitale présentant {', '.join(anomalies[:2])} nécessitant une prise en charge immédiate."
            else:
                return f"Patient présentant {motif} avec signes de détresse vitale nécessitant une intervention médicale immédiate."

        elif gravity_level == "JAUNE":
            if anomalies:
                return f"Patient nécessitant une prise en charge rapide en raison de {', '.join(anomalies[:2])} et {motif}."
            else:
                return f"Patient présentant {motif} nécessitant une évaluation médicale rapide."

        elif gravity_level == "VERT":
            return f"Patient stable présentant {motif} pouvant attendre une consultation dans un délai standard."

        else:  # GRIS
            return f"Patient stable sans signe de détresse présentant {motif}, prise en charge différée possible."
