from pydantic import BaseModel, Field
from typing import Optional, List

class ExtractedConstantes(BaseModel):
    """Tout est optionnel car on ne sait pas ce que la conversation contient"""
    frequence_cardiaque: Optional[int] = Field(None, description="Rythme cardiaque en bpm")
    pression_systolique: Optional[int] = Field(None, description="Pression artérielle systolique (le grand chiffre)")
    pression_diastolique: Optional[int] = Field(None, description="Pression artérielle diastolique (le petit chiffre)")
    frequence_respiratoire: Optional[int] = Field(None, description="Cycles par minute")
    temperature: Optional[float] = Field(None, description="Température en degrés Celsius")
    saturation_oxygene: Optional[int] = Field(None, description="SpO2 en pourcentage")
    echelle_douleur: Optional[int] = Field(None, description="Note de 0 à 10 donnée par le patient")
    glycemie: Optional[float] = Field(None, description="Glycémie capillaire en g/L")
    glasgow: Optional[int] = Field(None, description="Score de Glasgow (3-15)")

class ExtractedPatient(BaseModel):
    age: Optional[int] = Field(None, description="Âge du patient si mentionné")
    sexe: Optional[str] = Field(None, description="'M' ou 'F' selon le contexte de la discussion ('Bonjour Monsieur', accords gramaticaux etc)")
    motif_consultation: Optional[str] = Field(None, description="La raison principale de la venue")
    duree_symptomes: Optional[str] = Field(None, description="Depuis quand les symptômes sont présents (ex: '2 heures', '3 jours')")
    antecedents: Optional[List[str]] = Field(default_factory=list, description="Liste des antécédents médicaux cités")
    traitements: Optional[List[str]] = Field(default_factory=list, description="Médicaments actuels")
    
    # Nested objects
    constantes: ExtractedConstantes = Field(default_factory=ExtractedConstantes)
    
    # Méta-analyse (très utile pour le RAG ensuite !)
    missing_critical_info: List[str] = Field(
        default_factory=list, 
        description="Liste des informations vitales manquantes que l'infirmier DEVRAIT demander (ex: 'douleur', 'température')"
    )