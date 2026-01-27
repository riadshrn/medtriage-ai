import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List
from src.api.schemas.extraction import ExtractedPatient, ExtractedConstantes # Ton modèle Pydantic existant

# --- CONFIGURATION RAG ---
DB_PATH_DOCKER = "/app/data/vector_db"

# Initialisation du client (Lazy loading pour éviter de bloquer le démarrage si la DB n'est pas prête)
_chroma_client = None
_collection = None

def get_knowledge_base():
    """Singleton pour la connexion ChromaDB"""
    global _chroma_client, _collection
    
    if _collection is None:
        # On utilise le même modèle d'embedding que lors de l'ingestion
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        try:
            _chroma_client = chromadb.PersistentClient(path=DB_PATH_DOCKER)
            _collection = _chroma_client.get_collection(
                name="medical_knowledge", 
                embedding_function=ef
            )
            print(f"✅ ChromaDB connecté : {_collection.count()} documents chargés.")
        except Exception as e:
            print(f"⚠️ Erreur connexion ChromaDB : {e}")
            return None
            
    return _collection

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


# IMPORTANT : Dans les nouvelles versions de pydantic-ai, les tools n'utilisent plus RunContext
# Les tools sont maintenant de simples fonctions async sans contexte explicite

async def search_medical_protocol(symptome: str) -> str:
    """
    Cherche dans la base de connaissances médicale (Protocoles & Cas Similaires).
    Utilise cette fonction pour vérifier la gravité d'un symptôme ou les actions recommandées.
    
    Args:
        symptome: Le symptôme ou la condition médicale à rechercher
        
    Returns:
        Contexte médical pertinent trouvé dans la base de connaissances
    """
    collection = get_knowledge_base()
    
    if not collection:
        return "Erreur technique : Base de connaissances indisponible."
        
    print(f"🔎 Recherche RAG pour : {symptome}")
    
    results = collection.query(
        query_texts=[symptome],
        n_results=3 # On récupère les 3 morceaux les plus pertinents
    )
    
    # Formatage de la réponse pour l'LLM
    context_text = ""
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            source_type = meta.get('source', 'inconnu')
            category = meta.get('category', '')
            
            context_text += f"\n--- SOURCE ({source_type} / {category}) ---\n{doc}\n"
    else:
        context_text = "Aucune information spécifique trouvée dans les protocoles."
        
    return context_text


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