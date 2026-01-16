"""
Templates de prompts pour la génération de justifications.
"""

from typing import Dict


class PromptTemplates:
    """
    Templates de prompts pour le système RAG.

    Fournit des templates structurés pour guider le LLM
    dans la génération de justifications médicales.
    """

    SYSTEM_PROMPT = """Tu es un assistant médical expert en triage aux urgences.
Ta mission est d'aider les infirmiers à comprendre les décisions de classification des patients.

Règles importantes :
- Tu es un OUTIL D'AIDE À LA DÉCISION, pas un système de diagnostic
- Tu dois justifier les décisions de manière claire et concise
- Tu dois toujours t'appuyer sur les constantes vitales et les références médicales
- Tu dois mentionner les signes cliniques pertinents
- Tu ne dois pas inventer de symptômes non fournis
- Tu dois rester factuel et professionnel
"""

    JUSTIFICATION_TEMPLATE = """En tant qu'assistant médical, génère une justification COURTE (2-3 phrases maximum) pour la classification de ce patient en niveau {gravity_level}.

CONTEXTE DU PATIENT :
- Âge : {age} ans
- Sexe : {sexe}
- Motif : {motif}

CONSTANTES VITALES :
- Fréquence cardiaque : {fc} bpm
- Pression artérielle : {pa_sys}/{pa_dia} mmHg
- Fréquence respiratoire : {fr} /min
- Température : {temp}°C
- SpO2 : {spo2}%
- Échelle de douleur : {douleur}/10

RÉFÉRENCES MÉDICALES PERTINENTES :
{medical_context}

NIVEAU PRÉDIT : {gravity_level}
CONFIANCE DU MODÈLE : {confidence:.0%}

Génère une justification médicale CONCISE (2-3 phrases) expliquant pourquoi ce patient est classé en {gravity_level}.
La justification doit :
1. Mentionner les constantes vitales anormales (si présentes)
2. Faire référence au motif de consultation
3. Justifier le niveau de priorité attribué
4. Rester factuelle et basée sur les données fournies

JUSTIFICATION :"""

    SIMPLE_JUSTIFICATION_TEMPLATE = """Patient : {age} ans, {sexe}
Motif : {motif}
Niveau : {gravity_level}

Constantes :
FC={fc}, PA={pa_sys}/{pa_dia}, FR={fr}, T°={temp}, SpO2={spo2}%, Douleur={douleur}/10

Contexte médical :
{medical_context}

Justification médicale courte (2-3 phrases) pour niveau {gravity_level} :"""

    @staticmethod
    def format_justification_prompt(
        patient_data: Dict,
        gravity_level: str,
        confidence: float,
        medical_context: str,
    ) -> str:
        """
        Formate le prompt pour la génération de justification.

        Args:
            patient_data: Données du patient
            gravity_level: Niveau de gravité prédit
            confidence: Score de confiance
            medical_context: Contexte médical récupéré par RAG

        Returns:
            str: Prompt formaté
        """
        # Extraction des constantes
        constantes = patient_data.get("constantes", {})

        return PromptTemplates.JUSTIFICATION_TEMPLATE.format(
            gravity_level=gravity_level,
            age=patient_data.get("age", "?"),
            sexe=patient_data.get("sexe", "?"),
            motif=patient_data.get("motif_consultation", "?"),
            fc=constantes.get("frequence_cardiaque", "?"),
            pa_sys=constantes.get("pression_systolique", "?"),
            pa_dia=constantes.get("pression_diastolique", "?"),
            fr=constantes.get("frequence_respiratoire", "?"),
            temp=constantes.get("temperature", "?"),
            spo2=constantes.get("saturation_oxygene", "?"),
            douleur=constantes.get("echelle_douleur", "?"),
            confidence=confidence,
            medical_context=medical_context,
        )

    @staticmethod
    def format_simple_prompt(
        patient_data: Dict,
        gravity_level: str,
        medical_context: str,
    ) -> str:
        """
        Formate un prompt simplifié (plus court, pour modèles locaux).

        Args:
            patient_data: Données du patient
            gravity_level: Niveau de gravité
            medical_context: Contexte médical

        Returns:
            str: Prompt formaté
        """
        constantes = patient_data.get("constantes", {})

        return PromptTemplates.SIMPLE_JUSTIFICATION_TEMPLATE.format(
            age=patient_data.get("age", "?"),
            sexe=patient_data.get("sexe", "?"),
            motif=patient_data.get("motif_consultation", "?"),
            gravity_level=gravity_level,
            fc=constantes.get("frequence_cardiaque", "?"),
            pa_sys=constantes.get("pression_systolique", "?"),
            pa_dia=constantes.get("pression_diastolique", "?"),
            fr=constantes.get("frequence_respiratoire", "?"),
            temp=constantes.get("temperature", "?"),
            spo2=constantes.get("saturation_oxygene", "?"),
            douleur=constantes.get("echelle_douleur", "?"),
            medical_context=medical_context,
        )
