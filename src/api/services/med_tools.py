import os
import chromadb
from chromadb.utils import embedding_functions
from dataclasses import dataclass
from typing import Union, List
from src.api.schemas.extraction import ExtractedPatient, ExtractedConstantes # Ton modèle Pydantic existant

DB_PATH = os.path.join(os.getcwd(), "data", "vector_db")
COLLECTION_NAME = "medical_knowledge"

# Initialisation Globale (pour la performance)
print(f"🔌 Chargement du modèle d'embedding et connexion à ChromaDB à {DB_PATH}...")

try:
    # 1. Le modèle doit être STRICTEMENT le même que dans ingest.py
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    # 2. Connexion au client (Mode Persistant)
    client = chromadb.PersistentClient(path=DB_PATH)

    # 3. Récupération de la collection
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
    print("✅ RAG Service: Base de connaissances chargée avec succès.")

except Exception as e:
    print(f"⚠️ RAG Service: Impossible de charger la base vectorielle. Erreur: {e}")
    collection = None

# Liste définie côté Code (Single Source of Truth)
REQUIRED_FOR_ML = {
    "age", "sexe", 
    "constantes.frequence_cardiaque", 
    "constantes.pression_systolique", 
    "constantes.pression_diastolique", 
    "constantes.temperature", 
    "constantes.saturation_oxygene", 
    "constantes.frequence_respiratoire"
}


# 1. On définit la structure de notre "Mémoire Partagée"
@dataclass
class AgentState:
    patient_data: ExtractedPatient

async def search_medical_protocol(symptome: str) -> str:
    """
    Cherche dans la base de connaissances médicale (RAG) les protocoles ou cas similaires.
    Args:
        symptome: Le symptôme principal, la situation ou la question médicale.
    Returns:
        Un texte consolidé contenant les règles et contextes trouvés.
    """
    if collection is None:
        return "ERREUR TECHNIQUE : La base de connaissances est inaccessible."

    try:
        # On interroge la base (On récupère les 3 résultats les plus proches)
        results = collection.query(
            query_texts=[symptome],
            n_results=3
        )
        
        # Formatage de la réponse pour l'Agent
        # Chroma renvoie une liste de listes (car on peut envoyer plusieurs query_texts)
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        context_text = f"--- RÉSULTATS DE LA RECHERCHE POUR : '{symptome}' ---\n"
        
        for i, doc in enumerate(documents):
            meta = metadatas[i]
            source_type = meta.get('source', 'inconnu')
            titre = meta.get('topic', 'Sans titre')
            
            context_text += f"\n[SOURCE {i+1} : {source_type} - {titre}]\n{doc}\n"
            print(context_text)
            
        return context_text

    except Exception as e:
        return f"Erreur lors de la recherche dans le protocole : {str(e)}"

async def check_completeness_for_ml(found_fields: List[str]) -> str:
    """
    Vérifie si les données extraites sont suffisantes pour l'algorithme de prédiction.
    Args:
        found_fields: Liste des champs identifiés (ex: ['age', 'douleur', 'temperature']).
    Returns:
        Un message indiquant les variables manquantes ou un succès.
    """
    # Normalisation simple pour la comparaison
    found_set = set(f.lower() for f in found_fields)
    
    # On regarde ce qui manque
    missing = []
    for req in REQUIRED_FOR_ML:
        # On gère le cas "constantes.temperature" vs juste "temperature"
        key_check = req.split('.')[-1] 
        if key_check not in found_set and req not in found_set:
            missing.append(req)
            
    if not missing:
        return "✅ TOUTES les données requises pour le ML sont présentes."
    else:
        return f"⚠️ ALERTE ML - Variables manquantes pour l'algorithme : {', '.join(missing)}. Ajoute-les à 'missing_info'."