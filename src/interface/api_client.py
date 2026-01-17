"""
Client API pour communiquer avec le backend FastAPI

Ce module permet à l'interface Streamlit de consommer l'API REST.
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class TriageResult:
    """Résultat du triage"""
    prediction_id: int
    gravity_level: str
    french_triage_level: str
    confidence_score: float
    ml_score: float
    delai_prise_en_charge: str
    orientation: str
    justification: str
    red_flags: List[str]
    recommendations: List[str]
    model_version: str
    processing_time_ms: float


class APIClient:
    """
    Client pour l'API RedFlag-AI

    Usage:
        client = APIClient()
        result = client.triage(patient_data)
        client.submit_feedback(prediction_id, validated_level)
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL", "http://localhost:8000")
        self.timeout = 30.0

    def _get_client(self) -> httpx.Client:
        """Retourne un client HTTP configuré"""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def health_check(self) -> Dict[str, Any]:
        """Vérifie l'état de l'API"""
        try:
            with self._get_client() as client:
                response = client.get("/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def triage(
        self,
        age: int,
        sexe: str,
        motif_consultation: str,
        constantes: Dict[str, Any],
        antecedents: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        use_rag: bool = True
    ) -> TriageResult:
        """
        Effectue le triage d'un patient via l'API

        Args:
            age: Âge du patient
            sexe: Sexe (M/F)
            motif_consultation: Motif de consultation
            constantes: Dict des constantes vitales
            antecedents: Liste des antécédents (optionnel)
            allergies: Liste des allergies (optionnel)
            use_rag: Utiliser le RAG (défaut: True)

        Returns:
            TriageResult avec le niveau de gravité et les recommandations
        """
        payload = {
            "age": age,
            "sexe": sexe,
            "motif_consultation": motif_consultation,
            "constantes": constantes,
            "antecedents": antecedents,
            "allergies": allergies
        }

        with self._get_client() as client:
            response = client.post(
                "/api/v1/triage",
                json=payload,
                params={"use_rag": use_rag}
            )
            response.raise_for_status()
            data = response.json()

            return TriageResult(
                prediction_id=data["prediction_id"],
                gravity_level=data["gravity_level"],
                french_triage_level=data["french_triage_level"],
                confidence_score=data["confidence_score"],
                ml_score=data["ml_score"],
                delai_prise_en_charge=data["delai_prise_en_charge"],
                orientation=data["orientation"],
                justification=data["justification"],
                red_flags=data.get("red_flags", []),
                recommendations=data.get("recommendations", []),
                model_version=data["model_version"],
                processing_time_ms=data["processing_time_ms"]
            )

    def submit_feedback(
        self,
        prediction_id: int,
        validated_level: str,
        is_correct: bool,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Soumet la validation infirmière

        Args:
            prediction_id: ID de la prédiction
            validated_level: Niveau validé (ROUGE, JAUNE, VERT, GRIS)
            is_correct: La prédiction était-elle correcte
            notes: Commentaires optionnels

        Returns:
            Dict avec le résultat de la soumission
        """
        payload = {
            "prediction_id": prediction_id,
            "validated_level": validated_level,
            "is_correct": is_correct,
            "notes": notes
        }

        with self._get_client() as client:
            response = client.post("/api/v1/feedback", json=payload)
            response.raise_for_status()
            return response.json()

    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """Récupère les statistiques de feedback"""
        with self._get_client() as client:
            response = client.get("/api/v1/feedback/stats", params={"days": days})
            response.raise_for_status()
            return response.json()

    def get_pending_validations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les prédictions en attente de validation"""
        with self._get_client() as client:
            response = client.get("/api/v1/feedback/pending", params={"limit": limit})
            response.raise_for_status()
            return response.json().get("pending_predictions", [])

    def get_models(self) -> Dict[str, Any]:
        """Liste les modèles disponibles"""
        with self._get_client() as client:
            response = client.get("/api/v1/models")
            response.raise_for_status()
            return response.json()

    def get_active_model(self) -> Dict[str, Any]:
        """Récupère le modèle actif"""
        with self._get_client() as client:
            response = client.get("/api/v1/models/active")
            response.raise_for_status()
            return response.json()

    def activate_model(self, model_id: int) -> Dict[str, Any]:
        """Active un modèle spécifique"""
        with self._get_client() as client:
            response = client.post(
                "/api/v1/models/activate",
                json={"model_id": model_id}
            )
            response.raise_for_status()
            return response.json()

    def retrain_model(
        self,
        use_feedback_data: bool = True,
        use_hf_datasets: bool = False,
        min_feedback_samples: int = 100
    ) -> Dict[str, Any]:
        """Lance le réentraînement du modèle"""
        payload = {
            "use_feedback_data": use_feedback_data,
            "use_hf_datasets": use_hf_datasets,
            "min_feedback_samples": min_feedback_samples
        }

        with self._get_client() as client:
            response = client.post("/api/v1/models/retrain", json=payload)
            response.raise_for_status()
            return response.json()

    def get_recent_predictions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les prédictions récentes"""
        with self._get_client() as client:
            response = client.get(
                "/api/v1/triage/history/recent",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json().get("predictions", [])


# Instance globale pour faciliter l'utilisation
_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Retourne l'instance du client API (singleton)"""
    global _client
    if _client is None:
        _client = APIClient()
    return _client
