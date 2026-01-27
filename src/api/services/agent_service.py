import os
import time
from pydantic_ai import Agent

# Imports mis à jour
from src.api.schemas.agent_io import AgentResponse 

class MedicalAgentService:
    def __init__(self):
        # Import des tools ici pour éviter les imports circulaires
        from src.api.services.med_tools import search_medical_protocol, check_completeness_for_ml
        
        model_name = os.getenv("LLM_MODEL", "mistral-small-latest")
        
        # Si la variable d'environnement contient un provider (ex: "mistral/mistral-small-latest")
        # on extrait juste le nom du modèle
        if "/" in model_name: 
            model_name = model_name.split("/")[-1]
        
        # Si le nom contient déjà le préfixe "mistral:", on l'utilise tel quel
        # Sinon on ajoute le préfixe
        if model_name.startswith("mistral:"):
            model_string = model_name
        else:
            model_string = f"mistral:{model_name}"
        
        # Créer l'agent avec les tools passés dans le constructeur
        self.agent = Agent(
            model_string,
            output_type=AgentResponse,
            tools=[search_medical_protocol, check_completeness_for_ml],  # <-- Tools dans le constructeur
            system_prompt=(
                "Tu es un Copilote de Régulation Médicale."
                "Ta mission : Analyser le cas clinique et préparer les données pour l'IA prédictive."
                "\n\n"
                "FLUX DE TRAVAIL (Respecte cet ordre) :"
                "\n1. 🧠 ANALYSE : Identifie les symptômes et données présentes dans le texte."
                "\n2. 📚 PROTOCOLE : Si un symptôme t'inquiète, interroge 'search_medical_protocol'."
                "\n3. ✅ VALIDATION TECHNIQUE : Appelle 'check_completeness_for_ml' avec la liste des infos que tu as trouvées pour savoir ce qu'il manque au modèle ML."
                "\n4. 📝 RÉDACTION : Génère la réponse finale."
                "\n\n"
                "RÈGLES DE REMPLISSAGE :"
                "\n- 'missing_info' : Combine les manques cliniques (liés au protocole) ET les manques techniques (relevés par l'outil de validation)."
                "\n- 'protocol_alert' : Remplis uniquement si le protocole médical indique une urgence ou une action spécifique."
            )
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
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'tool_name'):
                            args = getattr(part, 'args', {})
                            steps.append(f"🛠️ **Recherche RAG** : `{part.tool_name}`")
                        elif hasattr(part, 'content') and hasattr(msg, 'kind') and msg.kind == 'tool-return':
                             steps.append(f"✅ **Résultat** : {part.content[:80]}...")

            # Métriques
            usage = result.usage()
            impacts = self._estimate_impact(usage.request_tokens, usage.response_tokens, latency_s)

            # Extraction
            final_obj = result.data 

            return {
                # On éclate la réponse pour le frontend
                "missing_info": final_obj.missing_info,
                "protocol_alert": final_obj.protocol_alert,
                "extracted_data": final_obj.data.model_dump(),
                
                "reasoning_steps": steps,
                "metrics": impacts
            }
            
        except Exception as e:
            print(f"❌ CRASH AGENT: {e}")
            import traceback
            traceback.print_exc()
            return {
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