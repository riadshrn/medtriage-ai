from pydantic_ai import RunContext
from dataclasses import dataclass
from typing import Union, List
from api.schemas.extraction import ExtractedPatient, ExtractedConstantes # Ton modèle Pydantic existant

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

# 2. Outil RAG (Inchangé, il n'a pas besoin d'écrire)
async def search_medical_protocol(symptome: str) -> str:
    """Cherche dans la base de connaissances médicale."""
    # (Garde ton code mocké ou RAG ici)
    if "ventre" in symptome.lower():
        return "PROTOCOLE DOULEUR ABDOMINALE: Vérifier intensité, localisation, fièvre."
    return "Protocole standard : Prise de constantes complètes."

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