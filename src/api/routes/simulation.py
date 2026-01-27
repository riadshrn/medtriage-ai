"""
Module de routes pour la simulation de triage médical.

Ce module expose les endpoints nécessaires à la simulation interactive
d'un entretien infirmier-patient aux urgences, permettant l'entraînement
des infirmiers IOA au processus de triage.

Endpoints:
    - POST /patient-response : Génère une réponse de patient simulé via LLM
    - POST /suggest-questions : Propose des questions pertinentes pour le triage
    - POST /extraction/analyze : Analyse la conversation et extrait les données médicales
"""

import os
import time
from typing import Dict, List

import litellm
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.services.extraction_service import PatientExtractor

router = APIRouter()


class PatientResponseRequest(BaseModel):
    """
    Requête pour la génération d'une réponse de patient simulé.

    Attributes:
        persona: Description du profil du patient (âge, symptômes, personnalité)
        history: Historique des échanges infirmier/patient
        nurse_message: Question ou message de l'infirmier
    """

    persona: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    nurse_message: str


class QuestionSuggestionRequest(BaseModel):
    """
    Requête pour la génération de suggestions de questions.

    Attributes:
        missing_info: Liste des informations manquantes pour le triage
        history: Historique récent de la conversation
    """

    missing_info: List[str]
    history: List[Dict[str, str]] = Field(default_factory=list)


class TextAnalysisRequest(BaseModel):
    """
    Requête pour l'analyse d'une transcription de conversation.

    Attributes:
        text: Texte brut de la conversation à analyser
    """

    text: str


@router.post("/patient-response")
async def generate_patient_response(request: PatientResponseRequest) -> Dict:
    """
    Génère une réponse réaliste du patient simulé.

    Le patient simulé répond en fonction de son persona défini et
    du contexte de la conversation. Le comportement est calibré pour
    reproduire des interactions réalistes aux urgences.

    Args:
        request: Requête contenant le persona, l'historique et le message infirmier

    Returns:
        Dict contenant la réponse du patient et la latence de génération

    Raises:
        HTTPException: En cas d'erreur lors de l'appel au LLM
    """
    start_time = time.time()
    model = os.getenv("LLM_MODEL", "mistral/mistral-small-latest")

    history_text = "\n".join([
        f"{'Infirmier' if m.get('role') == 'user' else 'Patient'}: {m.get('content', '')}"
        for m in request.history[-6:]
    ])

    system_prompt = f"""Tu es un patient aux urgences. Voici ton profil:

{request.persona}

CONSIGNES:
- Réponds uniquement en tant que patient, de manière réaliste
- Utilise un langage naturel, parfois hésitant selon ton état
- Ne donne pas toutes les informations d'emblée, réponds aux questions posées
- Exprime tes émotions (anxiété, douleur, peur) de manière cohérente avec ton profil
- Limite tes réponses à 1-3 phrases
- Ne pose jamais de diagnostic, tu es le patient

IMPORTANT - CONSTANTES VITALES:
Quand l'infirmier te demande tes constantes (tension, pouls, température, saturation, douleur, etc.), tu dois donner les VALEURS NUMÉRIQUES PRÉCISES indiquées dans ton profil CONSTANTES.
Par exemple: "Ma tension est à 155/95" ou "J'ai 38.5 de fièvre" ou "La douleur c'est 8 sur 10".
L'infirmière vient de te prendre les constantes, tu peux donc les lui donner."""

    user_prompt = f"""Historique de la conversation:
{history_text}

L'infirmier demande: "{request.nurse_message}"

Ta réponse en tant que patient:"""

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        patient_response = response.choices[0].message.content.strip()
        latency_ms = (time.time() - start_time) * 1000

        return {
            "response": patient_response,
            "latency_ms": latency_ms
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@router.post("/suggest-questions")
async def suggest_questions(request: QuestionSuggestionRequest) -> Dict:
    """
    Génère des suggestions de questions adaptées au contexte.

    Les suggestions sont générées en fonction des informations manquantes
    pour le triage et du contexte de la conversation en cours.
    Priorité aux éléments critiques de la grille FRENCH.

    Args:
        request: Requête contenant les informations manquantes et l'historique

    Returns:
        Dict contenant une liste de 3 suggestions de questions
    """
    model = os.getenv("LLM_MODEL", "mistral/mistral-small-latest")

    missing_text = "\n".join([f"- {info}" for info in request.missing_info[:5]])
    history_text = "\n".join([
        f"{'Infirmier' if m.get('role') == 'user' else 'Patient'}: {m.get('content', '')}"
        for m in request.history[-4:]
    ])

    system_prompt = """Tu es un assistant pour infirmier IOA aux urgences.
Génère exactement 3 questions pertinentes que l'infirmier devrait poser.

CRITÈRES:
- Questions courtes et directes (maximum 15 mots)
- Adaptées au contexte de la conversation
- Priorité aux informations critiques pour le triage FRENCH
- Formulation professionnelle et accessible au patient"""

    user_prompt = f"""Informations manquantes pour le triage:
{missing_text}

Historique récent:
{history_text}

Génère 3 questions (une par ligne, sans numérotation):"""

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )

        content = response.choices[0].message.content.strip()
        suggestions = [
            line.strip().lstrip("-•0123456789.) ")
            for line in content.split("\n")
            if line.strip() and len(line.strip()) > 5
        ][:3]

        if len(suggestions) < 3:
            fallback = [
                "Pouvez-vous décrire votre douleur ?",
                "Depuis quand avez-vous ces symptômes ?",
                "Avez-vous des antécédents médicaux ?"
            ]
            suggestions.extend(fallback[len(suggestions):3])

        return {"suggestions": suggestions}

    except Exception:
        return {
            "suggestions": [
                "Qu'est-ce qui vous amène aux urgences ?",
                "Depuis quand avez-vous ces symptômes ?",
                "Avez-vous des antécédents médicaux ?"
            ]
        }


@router.post("/extraction/analyze")
async def analyze_text(request: TextAnalysisRequest) -> Dict:
    """
    Analyse une transcription et extrait les données médicales structurées.

    Utilise le service d'extraction pour identifier les informations
    pertinentes au triage: constantes vitales, motif de consultation,
    antécédents, etc.

    Args:
        request: Requête contenant le texte de la conversation

    Returns:
        Dict contenant les données extraites et les métriques de performance

    Raises:
        HTTPException: En cas d'erreur lors de l'extraction
    """
    try:
        extractor = PatientExtractor()
        extracted_data, metrics = extractor.extract_from_conversation(request.text)

        return {
            "extracted_data": extracted_data.model_dump(),
            "metrics": metrics.model_dump() if metrics else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction: {str(e)}")
