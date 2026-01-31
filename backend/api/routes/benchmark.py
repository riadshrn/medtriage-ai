"""
Routes pour le benchmark des modeles LLM.

Ce module expose les endpoints necessaires pour comparer les performances
des differents modeles Mistral sur les taches d'extraction, agent et simulation.
"""

import time
from typing import Dict, List

import litellm
from ecologits import EcoLogits
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.schemas.extraction import ExtractedPatient

# Initialisation EcoLogits pour le tracking environnemental
try:
    EcoLogits.init(providers="litellm", electricity_mix_zone="FRA")
    print("✅ EcoLogits initialisé pour Benchmark (Zone FRA)")
except Exception as e:
    print(f"⚠️ Warning EcoLogits Benchmark: {e}")

router = APIRouter()

# Configuration des modeles disponibles pour le benchmark
AVAILABLE_MODELS = {
    "ministral-3b-latest": "mistral/ministral-3b-latest",
    "mistral-small-latest": "mistral/mistral-small-latest",
    "mistral-medium-latest": "mistral/mistral-medium-latest",
    "mistral-large-latest": "mistral/mistral-large-latest"
}

# Prix des modeles (USD par million de tokens) - Source: https://mistral.ai/pricing
MODEL_PRICES = {
    "ministral-3b-latest": {"input": 0.04, "output": 0.04},
    "mistral-small-latest": {"input": 0.1, "output": 0.3},
    "mistral-medium-latest": {"input": 0.4, "output": 2.0},
    "mistral-large-latest": {"input": 2.0, "output": 6.0},
}


class BenchmarkExtractionRequest(BaseModel):
    """Requete pour le benchmark d'extraction."""
    text: str
    model: str = "mistral-small-latest"


class BenchmarkSimulationRequest(BaseModel):
    """Requete pour le benchmark de simulation patient."""
    persona: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    nurse_message: str
    model: str = "mistral-small-latest"


class BenchmarkAgentRequest(BaseModel):
    """Requete pour le benchmark de l'agent."""
    conversation: Dict
    model: str = "mistral-small-latest"


def calculate_price(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calcule le cout d'une requete."""
    clean_name = model.split("/")[-1] if "/" in model else model
    prices = MODEL_PRICES.get(clean_name, {"input": 0.1, "output": 0.3})
    input_cost = (prices["input"] / 1_000_000) * input_tokens
    output_cost = (prices["output"] / 1_000_000) * output_tokens
    return input_cost + output_cost


def get_energy_from_response(response) -> Dict:
    """
    Extrait les donnees environnementales depuis EcoLogits.
    Source officielle : https://github.com/genai-impact/ecologits
    """
    energy_kwh = None
    gwp_kgco2 = None

    if hasattr(response, "impacts") and response.impacts is not None:
        try:
            # EcoLogits retourne des valeurs min/max, on prend min par defaut
            energy_val = response.impacts.energy.value
            gwp_val = response.impacts.gwp.value
            energy_kwh = getattr(energy_val, "min", energy_val)
            gwp_kgco2 = getattr(gwp_val, "min", gwp_val)
            print(f"🌱 EcoLogits : {energy_kwh} kWh, {gwp_kgco2} kgCO2")
        except Exception as e:
            print(f"⚠️ Erreur lecture EcoLogits : {e}")

    return {
        "gwp_kgco2": gwp_kgco2,
        "energy_kwh": energy_kwh
    }


@router.post("/extraction")
async def benchmark_extraction(request: BenchmarkExtractionRequest) -> Dict:
    """
    Benchmark de l'extraction de donnees medicales avec un modele specifique.
    """
    model_name = request.model
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Modele non supporte: {model_name}")

    full_model = AVAILABLE_MODELS[model_name]
    start_time = time.time()

    try:
        # Prompt d'extraction
        schema_json = ExtractedPatient.model_json_schema()

        system_prompt = f"""Tu es un expert medical. Extrais les infos au format JSON STRICT.
Schema : {schema_json}
Regles : Cles exactes, null si absent, entiers pour chiffres."""

        user_prompt = f"Transcription :\n---\n{request.text}\n---\nGenere le JSON."

        response = litellm.completion(
            model=full_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        latency_s = time.time() - start_time
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = input_tokens + output_tokens

        # Calcul des metriques
        cost = calculate_price(model_name, input_tokens, output_tokens)
        energy_data = get_energy_from_response(response)

        return {
            "success": True,
            "model": model_name,
            "extracted_data": response.choices[0].message.content,
            "metrics": {
                "provider": "ecologits",
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_s": latency_s,
                "cost_usd": cost,
                "gwp_kgco2": energy_data["gwp_kgco2"],
                "energy_kwh": energy_data["energy_kwh"]
            }
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "error": str(e),
            "metrics": None
        }


@router.post("/simulation")
async def benchmark_simulation(request: BenchmarkSimulationRequest) -> Dict:
    """
    Benchmark de la simulation patient avec un modele specifique.
    """
    model_name = request.model
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Modele non supporte: {model_name}")

    full_model = AVAILABLE_MODELS[model_name]
    start_time = time.time()

    try:
        history_text = "\n".join([
            f"{'Infirmier' if m.get('role') == 'user' else 'Patient'}: {m.get('content', '')}"
            for m in request.history[-6:]
        ])

        system_prompt = f"""Tu es un patient aux urgences. Voici ton profil:

{request.persona}

CONSIGNES:
- Reponds uniquement en tant que patient, de maniere realiste
- Utilise un langage naturel, parfois hesitant selon ton etat
- Ne donne pas toutes les informations d'emblee, reponds aux questions posees
- Exprime tes emotions (anxiete, douleur, peur) de maniere coherente avec ton profil
- Limite tes reponses a 1-3 phrases"""

        user_prompt = f"""Historique de la conversation:
{history_text}

L'infirmier demande: "{request.nurse_message}"

Ta reponse en tant que patient:"""

        response = litellm.completion(
            model=full_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        latency_s = time.time() - start_time
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = input_tokens + output_tokens

        cost = calculate_price(model_name, input_tokens, output_tokens)
        energy_data = get_energy_from_response(response)

        return {
            "success": True,
            "model": model_name,
            "response": response.choices[0].message.content.strip(),
            "metrics": {
                "provider": "ecologits",
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_s": latency_s,
                "cost_usd": cost,
                "gwp_kgco2": energy_data["gwp_kgco2"],
                "energy_kwh": energy_data["energy_kwh"]
            }
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "error": str(e),
            "metrics": None
        }


@router.post("/agent")
async def benchmark_agent(request: BenchmarkAgentRequest) -> Dict:
    """
    Benchmark de l'agent de triage avec un modele specifique.
    Note: L'agent utilise PydanticAI qui ne supporte pas facilement le switch de modele.
    Cette route utilise une extraction enrichie comme proxy.
    """
    model_name = request.model
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Modele non supporte: {model_name}")

    full_model = AVAILABLE_MODELS[model_name]
    start_time = time.time()

    try:
        # Reconstruction du texte de la conversation
        messages = request.conversation.get("messages", [])
        full_text = "\n".join([
            f"{'Infirmier' if m.get('role') in ['infirmier', 'user'] else 'Patient'}: {m.get('content', '')}"
            for m in messages
        ])

        # Prompt d'analyse enrichi (simulation agent)
        system_prompt = """Tu es un Copilote de Regulation Medicale expert en triage.

MISSION : Analyse la conversation et determine :
1. Le niveau de criticite (ROUGE, JAUNE, VERT, GRIS)
2. Les informations manquantes critiques
3. Les alertes protocole eventuelles

Reponds en JSON avec les cles: criticity, missing_info (liste), protocol_alert (string ou null), justification (string)"""

        user_prompt = f"""Analyse cette conversation patient-infirmier:

{full_text}

Genere ton analyse en JSON:"""

        response = litellm.completion(
            model=full_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        latency_s = time.time() - start_time
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = input_tokens + output_tokens

        cost = calculate_price(model_name, input_tokens, output_tokens)
        energy_data = get_energy_from_response(response)

        return {
            "success": True,
            "model": model_name,
            "analysis": response.choices[0].message.content,
            "metrics": {
                "provider": "ecologits",
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_s": latency_s,
                "cost_usd": cost,
                "gwp_kgco2": energy_data["gwp_kgco2"],
                "energy_kwh": energy_data["energy_kwh"]
            }
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "error": str(e),
            "metrics": None
        }


@router.get("/models")
async def list_models() -> Dict:
    """Liste les modeles disponibles pour le benchmark."""
    return {
        "models": list(AVAILABLE_MODELS.keys()),
        "prices": MODEL_PRICES
    }
