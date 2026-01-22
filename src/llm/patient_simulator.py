"""
Simulateur de Patient basé sur LLM (Mistral API)
Génère des réponses réalistes pour l'interrogatoire médical
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Mistral API
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "1CSRbNFOoLoK8bMGyN77xnRpsjXKxpkE")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


@dataclass
class LLMResponse:
    """Réponse du LLM avec métadonnées"""
    content: str
    prompt_used: str
    model: str = "mistral-small-latest"
    tokens_used: int = 0
    latency_ms: float = 0.0


class PatientSimulator:
    """
    Simulateur de patient utilisant Mistral API.

    Usage:
        simulator = PatientSimulator()
        response = simulator.generate_response(persona, question, history)
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "mistral-small-latest",
        timeout: int = 60
    ):
        self.api_key = api_key or MISTRAL_API_KEY
        self.model = model
        self.timeout = timeout
        self._last_prompt = ""
        self._last_response = None

    def is_available(self) -> bool:
        """Vérifie si l'API Mistral est accessible"""
        if not self.api_key:
            return False
        try:
            response = requests.get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Mistral disponibles"""
        try:
            response = requests.get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except:
            pass
        return ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"]

    def build_system_prompt(self, persona: Dict) -> str:
        """Construit le prompt système pour le persona du patient"""

        age = persona.get("age", 45)
        sexe = "homme" if persona.get("sexe", "M") == "M" else "femme"
        symptomes = persona.get("symptomes", [])
        personnalite = persona.get("personnalite", "patient normal")
        constantes = persona.get("constantes", {})
        douleur = constantes.get('echelle_douleur', 5)

        system_prompt = f"""Tu joues le rôle d'un patient aux urgences. Réponds de manière réaliste et concise.

# TON PROFIL
- Âge : {age} ans
- Sexe : {sexe}
- Symptômes : {', '.join(symptomes) if symptomes else 'malaise général'}
- Niveau de douleur : {douleur}/10
- Personnalité : {personnalite}

# RÈGLES OBLIGATOIRES
- Réponds TOUJOURS en français
- Réponds en 1-2 phrases MAXIMUM
- Si on demande ton âge : réponds "{age} ans"
- Si on demande ton sexe : réponds "Je suis {'un homme' if sexe == 'homme' else 'une femme'}"
- Si on demande l'échelle de douleur (1 à 10) : réponds "{douleur} sur 10" puis décris brièvement
- Si on demande tes symptômes : décris {symptomes[0] if symptomes else 'ton malaise'}
- Ne donne JAMAIS de diagnostic médical
- Reste cohérent avec ton profil

# EXEMPLES DE BONNES RÉPONSES
Q: "Quel âge avez-vous ?" → "{age} ans."
Q: "Sur une échelle de 1 à 10 ?" → "{douleur} sur 10, c'est {'très douloureux' if douleur >= 7 else 'supportable' if douleur >= 4 else 'léger'}."
Q: "Où avez-vous mal ?" → "J'ai mal au niveau de... [localisation selon symptômes]"
"""
        return system_prompt

    def build_messages(self, persona: Dict, nurse_question: str, chat_history: List[Dict]) -> List[Dict]:
        """Construit les messages pour l'API Mistral"""
        messages = []

        # System prompt
        system_prompt = self.build_system_prompt(persona)
        messages.append({"role": "system", "content": system_prompt})

        # Historique de conversation (derniers 6 messages)
        for msg in chat_history[-6:]:
            if msg["role"] == "nurse":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "patient":
                messages.append({"role": "assistant", "content": msg["content"]})

        # Question actuelle
        messages.append({"role": "user", "content": nurse_question})

        return messages

    def generate_response(
        self,
        persona: Dict,
        nurse_question: str,
        chat_history: List[Dict]
    ) -> LLMResponse:
        """
        Génère une réponse du patient via Mistral API.

        Args:
            persona: Dictionnaire avec les infos du patient
            nurse_question: Question posée par l'infirmier
            chat_history: Historique de la conversation

        Returns:
            LLMResponse avec le contenu et les métadonnées
        """
        import time
        start_time = time.time()

        # Construire les messages
        messages = self.build_messages(persona, nurse_question, chat_history)

        # Stocker le prompt pour affichage
        self._last_prompt = self.build_system_prompt(persona) + f"\n\n[Question: {nurse_question}]"

        # Appeler Mistral API
        try:
            logger.info(f"Appel Mistral API avec modèle {self.model}")

            response = requests.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 150,
                    "top_p": 0.9,
                },
                timeout=self.timeout
            )

            latency = (time.time() - start_time) * 1000
            logger.info(f"Réponse Mistral: status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                # Nettoyer la réponse
                content = self._clean_response(content)

                self._last_response = LLMResponse(
                    content=content,
                    prompt_used=self._last_prompt,
                    model=self.model,
                    tokens_used=tokens_used,
                    latency_ms=latency
                )
                return self._last_response
            else:
                error_msg = response.json().get("error", {}).get("message", "Erreur inconnue")
                logger.error(f"Erreur Mistral API: {error_msg}")
                return LLMResponse(
                    content=f"*le patient semble confus* ... Je ne me sens pas bien...",
                    prompt_used=self._last_prompt,
                    model=self.model,
                    latency_ms=latency
                )

        except requests.exceptions.Timeout:
            return LLMResponse(
                content="*le patient met du temps à répondre* ... Excusez-moi, je suis un peu perdu...",
                prompt_used=self._last_prompt,
                model=self.model
            )
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                content="[Erreur: Impossible de contacter l'API Mistral]",
                prompt_used=self._last_prompt,
                model=self.model
            )
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            return LLMResponse(
                content=f"[Erreur: {str(e)}]",
                prompt_used=self._last_prompt,
                model=self.model
            )

    def _clean_response(self, response: str) -> str:
        """Nettoie la réponse du LLM"""
        # Supprimer les préfixes courants
        prefixes = ["Patient:", "Patient :", "Réponse:", "Réponse :"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()

        # Limiter à 3 phrases max
        sentences = response.split('.')
        if len(sentences) > 3:
            response = '.'.join(sentences[:3]) + '.'

        return response.strip()

    def get_last_prompt(self) -> str:
        """Retourne le dernier prompt utilisé (pour debug)"""
        return self._last_prompt

    def get_last_response(self) -> Optional[LLMResponse]:
        """Retourne la dernière réponse complète"""
        return self._last_response


class RuleBasedPatientSimulator:
    """Simulateur basé sur des règles (fallback si API indisponible)"""

    def __init__(self):
        self._last_prompt = "Mode règles - pas de prompt LLM"

    def is_available(self) -> bool:
        return True

    def generate_response(self, persona: Dict, nurse_question: str, chat_history: List[Dict]) -> LLMResponse:
        """Génère une réponse basée sur des règles simples"""
        from src.models.gravity_level import GravityLevel

        question_lower = nurse_question.lower()
        symptomes = persona.get("symptomes", [])
        age = persona.get("age", 45)
        sexe = persona.get("sexe", "M")
        personnalite = persona.get("personnalite", "").lower()
        level = persona.get("expected_level", GravityLevel.VERT)

        response = ""

        # Règles simples
        if any(w in question_lower for w in ["âge", "age", "ans"]):
            response = f"J'ai {age} ans."

        elif any(w in question_lower for w in ["homme", "femme", "sexe"]):
            response = "Je suis un homme." if sexe == "M" else "Je suis une femme."

        elif any(w in question_lower for w in ["symptôme", "mal", "douleur", "problème"]):
            if symptomes:
                if "anxieux" in personnalite:
                    response = f"Oh mon Dieu ! {symptomes[0]} ! C'est terrible !"
                else:
                    response = f"J'ai {symptomes[0].lower()}..."
            else:
                response = "Je ne me sens pas bien..."

        elif any(w in question_lower for w in ["depuis", "quand", "combien"]):
            response = "Ça a commencé il y a quelques heures..."

        elif any(w in question_lower for w in ["échelle", "sur 10", "intensité"]):
            pain = {
                GravityLevel.ROUGE: "10 sur 10 ! C'est insupportable !",
                GravityLevel.JAUNE: "7 ou 8 sur 10...",
                GravityLevel.VERT: "4 sur 10.",
                GravityLevel.GRIS: "2 sur 10."
            }
            response = pain.get(level, "5 sur 10...")

        elif any(w in question_lower for w in ["antécédent", "médicament", "allergie"]):
            response = "Non, pas d'antécédents particuliers."

        else:
            response = "Je ne sais pas trop... je me sens mal..."

        self._last_prompt = f"[Mode règles] Question: {nurse_question}"

        return LLMResponse(
            content=response,
            prompt_used=self._last_prompt,
            model="rule-based",
            tokens_used=0,
            latency_ms=0
        )

    def get_last_prompt(self) -> str:
        return self._last_prompt


def get_patient_simulator(use_mistral: bool = True) -> PatientSimulator:
    """Factory pour obtenir le bon simulateur"""
    if use_mistral:
        simulator = PatientSimulator()
        if simulator.is_available():
            return simulator
    return RuleBasedPatientSimulator()
