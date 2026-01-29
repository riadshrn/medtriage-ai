import os
import time
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

# Imports mis à jour
from api.services.med_tools import search_medical_protocol, check_completeness_for_ml
from api.schemas.agent_io import AgentResponse 

class MedicalAgentService:
    def __init__(self):
        model_name = os.getenv("LLM_MODEL", "mistral-small-latest")
        if "/" in model_name:
            model_name = model_name.split("/")[-1]

        self.model_name = model_name  # Stocker pour les métriques
        self.provider = "Mistral"
        self.model = MistralModel(model_name)
        
        self.agent = Agent(
            self.model,
            result_type=AgentResponse, # <-- L'Agent va maintenant remplir tes 3 champs
            
            system_prompt=(
                "Tu es un Copilote de Régulation Médicale."
                "Mission : récupérer les données médicales du patient pour assister l'infirmier dans son triage du patient."
                
                "FLUX DE TRAVAIL (Respecte cet ordre) :"
                "1. 🧠 ANALYSE : Identifie les symptômes et données présentes dans le texte."
                "2. 📚 PROTOCOLE (RAG) : Utilise ton outil de recherche pour trouver le protocole médical correspondant aux symptômes."
                "3. 🎨 CLASSIFICATION : En te basant sur le protocole trouvé (ou tes connaissances si le protocole est muet), détermine la couleur de triage (ROUGE, JAUNE, VERT, GRIS)."
                "4. ✅ VALIDATION TECHNIQUE : Appelle 'check_completeness_for_ml' avec les infos trouvées."
                "5. 📝 RÉDACTION : Génère le json final."

                """
                "RÈGLES DE REMPLISSAGE :"
                "- 'missing_info' : Combine les manques cliniques (liés au protocole) ET les manques techniques (relevés par l'outil de validation)."
                "- 'protocol_alert' : Remplis uniquement si le protocole médical indique une urgence ou une action spécifique."
                """
            ),
            tools=[search_medical_protocol, check_completeness_for_ml] 
        )

    def _estimate_impact(self, input_tok: int, output_tok: int, latency_s: float):
        """
        Calcul Scientifique (R²=1.000) basé sur la Régression Multiple.
        Formule : CO2 = a*Tokens + b*Latence + c
        """
        total_tokens = input_tok + output_tok
        
        # --- COEFFICIENTS CALIBRÉS (Mistral Small / FRA) ---
        COEFF_TOKENS  = 0.002726 # mg/token
        COEFF_LATENCY = 0.180694 # mg/seconde
        INTERCEPT     = -0.0291  # mg

        # 1. Calcul GWP (mg -> conversion kg pour stockage)
        gwp_mg = (total_tokens * COEFF_TOKENS) + (latency_s * COEFF_LATENCY) + INTERCEPT
        gwp_mg = max(0.0, gwp_mg) 
        gwp_kg = gwp_mg / 1e6

        # 2. Estimation Coût ($0.1 / 1M tokens)
        cost = (total_tokens / 1_000_000) * 0.10
        
        # 3. Energie (Ratio France : 1 kWh ≈ 0.055 kgCO2)
        energy_kwh = gwp_kg / 0.055 

        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "input_tokens": input_tok,
            "output_tokens": output_tok,
            "total_tokens": total_tokens,
            "latency_s": latency_s,
            "cost_usd": cost,
            "gwp_kgco2": gwp_kg,
            "energy_kwh": energy_kwh
        }
    
    def _check_ml_constraints(self, data: dict, current_missing: list) -> list:
        """
        Vérifie si les champs obligatoires pour le ML sont présents.
        Si non, les ajoute à la liste des infos manquantes.
        """
        missing_technical = []
        constantes = data.get('constantes', {})

        for field_path, human_name in self.ML_REQUIRED_FIELDS.items():
            val = None
            
            # Récupération de la valeur (support des niveaux imbriqués comme 'constantes.temp')
            if "." in field_path:
                parent, child = field_path.split(".")
                val = constantes.get(child)
            else:
                val = data.get(field_path)

            # Si la valeur est None (ou vide), c'est un manque technique
            if val is None:
                # On vérifie si l'agent ne l'a pas déjà demandé (pour éviter les doublons)
                # On fait une vérif simple sur le texte
                already_asked = any(human_name.lower() in q.lower() for q in current_missing)
                if not already_asked:
                    missing_technical.append(f"{human_name} (Requis pour l'IA Prédictive)")
        
        # On fusionne : D'abord les manques cliniques (Agent), puis les manques techniques (Python)
        return current_missing + missing_technical

    async def analyze_with_reasoning(self, full_text: str):
        try:
            start_time = time.time()
            
            # L'Agent génère l'objet AgentResponse
            result = await self.agent.run(f"Analyse ce patient :\n{full_text}")
            
            end_time = time.time()
            latency_s = end_time - start_time

            # Récupération Logs Outils
            steps = []
            for msg in result.new_messages():
                if not hasattr(msg, 'parts'):
                    continue
                    
                for part in msg.parts:
                    # CASE 1: The Model requests a tool execution
                    # Seen in logs: part_kind='tool-call'
                    if part.part_kind == 'tool-call':
                        tool_name = part.tool_name
                        args = part.args # It is a JSON string in your logs
                        
                        # 'final_result' is the internal tool PydanticAI uses to return the typed response
                        if tool_name == 'final_result':
                             steps.append("🏁 **Finalisation** : Generating structured response.")
                        else:
                             steps.append(f"🛠️ **Agent Call** `{tool_name}`\n   ❓ Args: {args}")

                    # CASE 2: The Tool returns data to the Model
                    # Seen in logs: part_kind='tool-return'
                    elif part.part_kind == 'tool-return':
                        tool_name = part.tool_name
                        content = part.content
                        
                        # Truncate long content for UI readability
                        content_str = str(content)
                        if len(content_str) > 500:
                            content_str = content_str[:500] + " [...]"
                        
                        steps.append(f"✅ **DB Response** ({tool_name}) :\n   {content_str}")
            # Métriques
            usage = result.usage()
            impacts = self._estimate_impact(usage.request_tokens, usage.response_tokens, latency_s)

            # Extraction
            final_obj = result.data 

            return {
                "criticity": final_obj.criticity, 
                "missing_info": final_obj.missing_info,
                "protocol_alert": final_obj.protocol_alert,
                "extracted_data": final_obj.data.model_dump(),
                
                "reasoning_steps": steps,
                "metrics": impacts
            }
            
        except Exception as e:
            print(f"❌ CRASH AGENT: {e}")
            return {
                "criticity": "GRIS", # Valeur par défaut en cas de crash
                "extracted_data": None,
                "missing_info": [],
                "protocol_alert": "Erreur système",
                "reasoning_steps": [f"❌ Erreur : {str(e)}"],
                "metrics": None
            }

# Singleton
_agent_instance = None
def get_agent_service():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MedicalAgentService()
    return _agent_instance