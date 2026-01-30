"""
Routes API pour l'historique des triages.

Endpoints:
- GET /history/list : Liste tous les triages
- GET /history/{prediction_id} : Détails d'un triage
- POST /history/save : Enregistre un nouveau triage
- GET /history/stats : Statistiques globales
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["Triage History"])

# Chemin vers le fichier d'historique
HISTORY_PATH = Path(__file__).parent.parent.parent / "data" / "history.json"


# =============================================================================
# SCHEMAS
# =============================================================================

class TriageHistoryEntry(BaseModel):
    """Entrée d'historique de triage."""
    prediction_id: str
    timestamp: str
    source: str  # "accueil", "simulation", "api"
    filename: Optional[str] = None

    # Résultat du triage
    gravity_level: str
    french_triage_level: Optional[str] = None
    confidence_score: Optional[float] = None
    orientation: Optional[str] = None
    delai_prise_en_charge: Optional[str] = None

    # Données patient
    patient_input: Optional[Dict] = None
    extracted_data: Optional[Dict] = None

    # Métadonnées
    model_version: Optional[str] = None
    ml_available: Optional[bool] = None

    # Feedback (si donné)
    feedback_given: bool = False
    feedback_type: Optional[str] = None
    corrected_gravity: Optional[str] = None


class SaveTriageRequest(BaseModel):
    """Requête pour sauvegarder un triage."""
    source: str
    filename: Optional[str] = None
    gravity_level: str
    french_triage_level: Optional[str] = None
    confidence_score: Optional[float] = None
    orientation: Optional[str] = None
    delai_prise_en_charge: Optional[str] = None
    patient_input: Optional[Dict] = None
    extracted_data: Optional[Dict] = None
    model_version: Optional[str] = None
    ml_available: Optional[bool] = None
    justification: Optional[str] = None
    red_flags: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class HistoryStats(BaseModel):
    """Statistiques de l'historique."""
    total_triages: int
    by_gravity: Dict[str, int]
    by_source: Dict[str, int]
    feedbacks_given: int
    last_triage_date: Optional[str] = None


# =============================================================================
# HELPERS
# =============================================================================

def load_history() -> List[Dict]:
    """Charge l'historique depuis le fichier JSON."""
    try:
        if HISTORY_PATH.exists():
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'historique: {e}")
    return []


def save_history(history: List[Dict]) -> bool:
    """Sauvegarde l'historique dans le fichier JSON."""
    try:
        # S'assurer que le dossier existe
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")
        return False


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/list")
async def list_history(limit: int = 50, offset: int = 0) -> Dict:
    """
    Liste l'historique des triages.

    Args:
        limit: Nombre max d'entrées à retourner
        offset: Décalage pour la pagination
    """
    history = load_history()

    # Trier par date décroissante
    history_sorted = sorted(
        history,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )

    total = len(history_sorted)
    entries = history_sorted[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entries": entries
    }


@router.get("/entry/{prediction_id}")
async def get_history_entry(prediction_id: str) -> Dict:
    """Récupère une entrée spécifique de l'historique."""
    history = load_history()

    for entry in history:
        if entry.get('prediction_id') == prediction_id:
            return entry

    raise HTTPException(status_code=404, detail="Entrée non trouvée")


@router.post("/save")
async def save_triage(request: SaveTriageRequest) -> Dict:
    """
    Enregistre un nouveau triage dans l'historique.

    Appelé par le frontend après chaque triage (Accueil ou Mode Interactif).
    """
    history = load_history()

    # Créer l'entrée
    prediction_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    entry = {
        "prediction_id": prediction_id,
        "timestamp": timestamp,
        "source": request.source,
        "filename": request.filename,
        "gravity_level": request.gravity_level,
        "french_triage_level": request.french_triage_level,
        "confidence_score": request.confidence_score,
        "orientation": request.orientation,
        "delai_prise_en_charge": request.delai_prise_en_charge,
        "patient_input": request.patient_input,
        "extracted_data": request.extracted_data,
        "model_version": request.model_version or "hybrid-v1",
        "ml_available": request.ml_available,
        "justification": request.justification,
        "red_flags": request.red_flags,
        "recommendations": request.recommendations,
        "feedback_given": False,
        "feedback_type": None,
        "corrected_gravity": None
    }

    # Ajouter au début de la liste
    history.insert(0, entry)

    # Limiter à 1000 entrées max
    if len(history) > 1000:
        history = history[:1000]

    if save_history(history):
        logger.info(f"Triage sauvegardé: {prediction_id}")
        return {
            "status": "success",
            "prediction_id": prediction_id,
            "timestamp": timestamp
        }
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")


@router.patch("/entry/{prediction_id}/feedback")
async def update_feedback(prediction_id: str, feedback_type: str, corrected_gravity: Optional[str] = None) -> Dict:
    """Met à jour une entrée avec le feedback."""
    history = load_history()

    for entry in history:
        if entry.get('prediction_id') == prediction_id:
            entry['feedback_given'] = True
            entry['feedback_type'] = feedback_type
            entry['corrected_gravity'] = corrected_gravity

            if save_history(history):
                return {"status": "success", "message": "Feedback enregistré"}
            else:
                raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    raise HTTPException(status_code=404, detail="Entrée non trouvée")


@router.get("/stats", response_model=HistoryStats)
async def get_stats() -> HistoryStats:
    """Retourne les statistiques de l'historique."""
    history = load_history()

    by_gravity = {}
    by_source = {}
    feedbacks_given = 0
    last_date = None

    for entry in history:
        # Par gravité
        gravity = entry.get('gravity_level', 'GRIS')
        by_gravity[gravity] = by_gravity.get(gravity, 0) + 1

        # Par source
        source = entry.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1

        # Feedbacks
        if entry.get('feedback_given'):
            feedbacks_given += 1

        # Dernière date
        timestamp = entry.get('timestamp')
        if timestamp and (last_date is None or timestamp > last_date):
            last_date = timestamp

    return HistoryStats(
        total_triages=len(history),
        by_gravity=by_gravity,
        by_source=by_source,
        feedbacks_given=feedbacks_given,
        last_triage_date=last_date
    )


@router.delete("/clear")
async def clear_history() -> Dict:
    """Efface tout l'historique (admin only)."""
    if save_history([]):
        return {"status": "success", "message": "Historique effacé"}
    raise HTTPException(status_code=500, detail="Erreur lors de l'effacement")
