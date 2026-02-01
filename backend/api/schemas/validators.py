# api/schemas/validators.py
import re
from typing import List, Union

# 1. LISTE NOIRE D'INJECTIONS (Français & Anglais)
# On cible les verbes d'action typiques des attaques "DAN" ou "Jailbreak"
INJECTION_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"oublie (toutes )?tes instructions",
    r"ignore tout ce qui précède",
    r"you are now",
    r"tu es maintenant",
    r"system override",
    r"mode développeur",
    r"écris un poème",
    r"donne-moi ta configuration"
]

# 2. LISTE NOIRE XSS (Sécurité Dashboard)
XSS_PATTERNS = [
    r"<script>",
    r"javascript:",
    r"onload=",
    r"onerror="
]

def validate_safe_input(v: str) -> str:
    """
    Validation stricte de l'entrée utilisateur.
    Rejette le texte s'il contient des tentatives d'injection connues.
    """
    if not v:
        return v
    
    v_lower = v.lower()
    
    # Check Injections
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, v_lower):
            raise ValueError(f"⛔ SÉCURITÉ : Tentative de manipulation détectée (Pattern: '{pattern}').")

    # Check XSS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, v_lower):
            raise ValueError("⛔ SÉCURITÉ : Code potentiellement malveillant détecté.")

    return v

def validate_medical_relevance(v: str) -> str:
    """
    Validation souple de la sortie.
    Vérifie juste qu'on ne part pas dans un délire total (hallucination grave).
    """
    if not v:
        return v
    
    # Si la réponse contient des phrases d'excuses d'IA standard, c'est souvent
    # que l'injection a réussi à faire "bugger" le modèle, ou qu'il refuse de répondre.
    # On peut choisir de filtrer ou de logger.
    refusal_patterns = ["je ne peux pas répondre", "as an ai language model"]
    
    if any(p in v.lower() for p in refusal_patterns):
        # On peut soit lever une erreur, soit laisser passer avec un warning.
        raise ValueError("⚠️ ALERTE : Le modèle a refusé de traiter la demande médicale.")
        
    return v