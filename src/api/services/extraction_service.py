import json
import os
import time
import litellm # <--- CHANGEMENT 1 : On importe tout le module
from ecologits import EcoLogits
from src.api.schemas.extraction import ExtractedPatient
from src.api.schemas.monitoring import LLMMetrics
from src.api.schemas.triage import PatientInput, ConstantesInput

# --- INITIALISATION GLOBALE ---
try:
    # On initialise AVANT d'utiliser litellm
    EcoLogits.init(providers="litellm", electricity_mix_zone="FRA")
    print("✅ EcoLogits initialisé pour LiteLLM (Zone FRA)")
except Exception as e:
    print(f"⚠️ Warning EcoLogits: {e}")
# -----------------------------

class PatientExtractor:
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.api_base = os.getenv("LLM_API_BASE", None)

    def _get_price_query(self, model: str, input_token: int, output_token: int) -> float:
        dict_price = {
            "mistral-small-latest": {"input": 0.1, "output": 0.3},
            "mistral-medium-latest": {"input": 0.4, "output": 2.0},
            "mistral-large-latest":  {"input": 0.5, "output": 1.5},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "ollama":        {"input": 0, "output": 0},
        }
        
        clean_name = model.split("/")[-1] if "/" in model else model
        price = dict_price.get(clean_name, dict_price.get("ollama"))
        
        if not price: return 0.0

        return ((price["input"] / 10**6) * input_token) + (
            (price["output"] / 10**6) * output_token
        )

    def extract_from_conversation(self, full_text: str) -> tuple[ExtractedPatient, LLMMetrics]:
        print(f"🧠 Appel LLM ({self.model})...")
        start_time = time.time()

        schema_json = json.dumps(ExtractedPatient.model_json_schema(), indent=2)

        system_prompt = f"""
        Tu es un expert médical. Extrais les infos au format JSON STRICT.
        Schéma : {schema_json}
        Règles : Clés exactes, null si absent, entiers pour chiffres.
        """
        
        user_prompt = f"Transcription :\n---\n{full_text}\n---\nGénère le JSON."

        try:
            # <--- CHANGEMENT 2 : On appelle via le module litellm.completion
            response = litellm.completion(
                model=self.model,
                api_base=self.api_base,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}, 
                temperature=0 
            )

            # Debugging
            if hasattr(response, "impacts"):
                print(f"🌱 Impacts détectés : {response.impacts}")
            else:
                print("⚠️ Aucun impact détecté (Toujours pas d'attribut impacts)")

            # 1. Parsing Données
            content = response.choices[0].message.content
            extracted_data = ExtractedPatient.model_validate_json(content)
            
            # 2. Parsing Métriques
            latency_ms = (time.time() - start_time) * 1000
            usage = response.usage
            input_tok = usage.prompt_tokens
            output_tok = usage.completion_tokens
            
            # Récupération EcoLogits
            energy = None
            gwp = None
            
            if hasattr(response, "impacts"):
                try:
                    energy = getattr(response.impacts.energy.value, "min", response.impacts.energy.value)
                    gwp = getattr(response.impacts.gwp.value, "min", response.impacts.gwp.value)
                except Exception as e:
                    print(f"⚠️ Erreur lecture impacts: {e}")

            cost = self._get_price_query(self.model, input_tok, output_tok)

            metrics = LLMMetrics(
                provider="litellm",
                model_name=self.model,
                input_tokens=input_tok,
                output_tokens=output_tok,
                total_tokens=input_tok + output_tok,
                latency_ms=latency_ms,
                cost_usd=cost,
                gwp_kgco2=gwp,
                energy_kwh=energy
            )

            return extracted_data, metrics

        except Exception as e:
            print(f"❌ Erreur Extraction : {e}")
            return ExtractedPatient(), LLMMetrics(
                provider="error", model_name=self.model, input_tokens=0, output_tokens=0, total_tokens=0, latency_ms=0, cost_usd=0
            )

    def to_triage_input(self, extracted: ExtractedPatient) -> PatientInput:
        c = extracted.constantes
        return PatientInput(
            age=extracted.age or 45,
            sexe=extracted.sexe or "M",
            motif_consultation=extracted.motif_consultation or "Non spécifié",
            antecedents=extracted.antecedents or [],
            constantes=ConstantesInput(
                frequence_cardiaque=c.frequence_cardiaque or 80,
                pression_systolique=c.pression_systolique or 120,
                pression_diastolique=c.pression_diastolique or 80,
                frequence_respiratoire=c.frequence_respiratoire or 16,
                temperature=c.temperature or 37.0,
                saturation_oxygene=c.saturation_oxygene or 98,
                echelle_douleur=c.echelle_douleur or 0,
                glycemie=c.glycemie,
                glasgow=c.glasgow or 15
            )
        )