"""
Utilitaires et gestion des erreurs pour l'interface Streamlit
"""

import streamlit as st
from typing import Any, Callable, Optional
import logging
from functools import wraps


# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_errors(func: Callable) -> Callable:
    """
    Décorateur pour gérer les erreurs dans les fonctions Streamlit
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            st.error(f"❌ Fichier introuvable : {e}")
            st.info("💡 Vérifiez que les modèles ML et les données sont bien présents.")
        except ValueError as e:
            logger.error(f"Value error: {e}")
            st.error(f"❌ Erreur de valeur : {e}")
            st.info("💡 Vérifiez que les données du patient sont valides.")
        except ImportError as e:
            logger.error(f"Import error: {e}")
            st.error(f"❌ Erreur d'import : {e}")
            st.info("💡 Installez les dépendances manquantes avec : `pip install -r requirements.txt`")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            st.error(f"❌ Erreur inattendue : {str(e)}")
            st.info("💡 Consultez les logs pour plus de détails.")

            # Mode debug : afficher la traceback complète
            if st.session_state.get("debug_mode", False):
                st.exception(e)

        return None
    return wrapper


def validate_patient_data(age: int, motif: str, constantes: dict) -> tuple[bool, Optional[str]]:
    """
    Valide les données d'un patient

    Returns:
        (is_valid, error_message)
    """

    # Validation de l'âge
    if not isinstance(age, int) or age < 0 or age > 120:
        return False, f"Âge invalide : {age}. Doit être entre 0 et 120 ans."

    # Validation du motif
    if not motif or len(motif.strip()) == 0:
        return False, "Le motif de consultation ne peut pas être vide."

    if len(motif) > 500:
        return False, f"Le motif de consultation est trop long ({len(motif)} caractères). Maximum 500."

    # Validation des constantes
    required_keys = [
        "frequence_cardiaque",
        "frequence_respiratoire",
        "saturation_oxygene",
        "pression_systolique",
        "pression_diastolique",
        "temperature",
        "echelle_douleur"
    ]

    for key in required_keys:
        if key not in constantes:
            return False, f"Constante manquante : {key}"

        value = constantes[key]
        if not isinstance(value, (int, float)):
            return False, f"Constante {key} doit être un nombre (reçu : {type(value).__name__})"

    # Validation des plages
    fc = constantes["frequence_cardiaque"]
    if not (20 <= fc <= 250):
        return False, f"Fréquence cardiaque hors limites : {fc} bpm (plage normale : 20-250)"

    fr = constantes["frequence_respiratoire"]
    if not (5 <= fr <= 60):
        return False, f"Fréquence respiratoire hors limites : {fr} /min (plage normale : 5-60)"

    spo2 = constantes["saturation_oxygene"]
    if not (50 <= spo2 <= 100):
        return False, f"Saturation en oxygène hors limites : {spo2}% (plage normale : 50-100)"

    tas = constantes["pression_systolique"]
    if not (40 <= tas <= 300):
        return False, f"Tension systolique hors limites : {tas} mmHg (plage normale : 40-300)"

    tad = constantes["pression_diastolique"]
    if not (20 <= tad <= 200):
        return False, f"Tension diastolique hors limites : {tad} mmHg (plage normale : 20-200)"

    temp = constantes["temperature"]
    if not (32.0 <= temp <= 45.0):
        return False, f"Température hors limites : {temp}°C (plage normale : 32-45)"

    echelle_douleur = constantes["echelle_douleur"]
    if not (0 <= echelle_douleur <= 10):
        return False, f"Score de douleur invalide : {echelle_douleur} (plage normale : 0-10)"

    # Validation de cohérence
    if tad >= tas:
        return False, f"La tension diastolique ({tad}) ne peut pas être supérieure ou égale à la systolique ({tas})"

    return True, None


def validate_constantes_coherence(constantes: dict) -> list[str]:
    """
    Vérifie la cohérence physiologique des constantes

    Returns:
        Liste des alertes (vide si tout est cohérent)
    """

    alerts = []

    fc = constantes["frequence_cardiaque"]
    fr = constantes["frequence_respiratoire"]
    spo2 = constantes["saturation_oxygene"]
    echelle_douleur = constantes["echelle_douleur"]

    # Alerte si bradycardie + hypoxie
    if fc < 50 and spo2 < 90:
        alerts.append("⚠️ Bradycardie + Hypoxie : situation critique probable")

    # Alerte si tachycardie + tachypnée
    if fc > 120 and fr > 25:
        alerts.append("⚠️ Tachycardie + Tachypnée : détresse respiratoire ou cardiaque ?")

    # Alerte si hypoxie sévère
    if spo2 < 85:
        alerts.append("🔴 HYPOXIE SÉVÈRE : oxygénothérapie urgente")

    # Alerte si douleur très intense
    if echelle_douleur >= 8:
        alerts.append("⚠️ DOULEUR INTENSE (≥ 8/10) : analgésie urgente nécessaire")

    return alerts


def format_triage_result_color(niveau: str) -> str:
    """
    Retourne la classe CSS pour le niveau de triage

    Args:
        niveau: Niveau de gravité (rouge, orange, jaune, vert, gris)

    Returns:
        Nom de la classe CSS
    """

    color_map = {
        "rouge": "triage-rouge",
        "orange": "triage-orange",
        "jaune": "triage-jaune",
        "vert": "triage-vert",
        "gris": "triage-gris"
    }

    return color_map.get(niveau.lower(), "triage-gris")


def get_emoji_for_level(niveau: str) -> str:
    """
    Retourne l'emoji correspondant au niveau de triage

    Args:
        niveau: Niveau de gravité

    Returns:
        Emoji
    """

    emoji_map = {
        "rouge": "🔴",
        "orange": "🟠",
        "jaune": "🟡",
        "vert": "🟢",
        "gris": "⚪"
    }

    return emoji_map.get(niveau.lower(), "❓")


def calculate_metrics_summary(results: list[dict]) -> dict:
    """
    Calcule un résumé des métriques à partir d'une liste de résultats

    Args:
        results: Liste de résultats de triage

    Returns:
        Dictionnaire avec les métriques agrégées
    """

    if not results:
        return {
            "total": 0,
            "accuracy": 0.0,
            "avg_latency_ms": 0.0,
            "avg_confidence": 0.0
        }

    total = len(results)
    correct = sum(1 for r in results if r.get("correct", False))
    latencies = [r.get("latency_ms", 0) for r in results]
    confidences = [r.get("confiance", 0) for r in results]

    return {
        "total": total,
        "accuracy": correct / total if total > 0 else 0.0,
        "avg_latency_ms": sum(latencies) / total if total > 0 else 0.0,
        "avg_confidence": sum(confidences) / total if total > 0 else 0.0,
        "min_latency_ms": min(latencies) if latencies else 0.0,
        "max_latency_ms": max(latencies) if latencies else 0.0
    }


def enable_debug_mode():
    """Active le mode debug dans la session"""
    st.session_state.debug_mode = True
    logger.setLevel(logging.DEBUG)


def disable_debug_mode():
    """Désactive le mode debug dans la session"""
    st.session_state.debug_mode = False
    logger.setLevel(logging.INFO)


def check_system_health() -> dict[str, bool]:
    """
    Vérifie l'état de santé du système

    Returns:
        Dictionnaire avec le statut de chaque composant
    """

    health = {
        "models_loaded": False,
        "rag_available": False,
        "data_accessible": False
    }

    try:
        # Vérifier si les modèles sont accessibles
        from pathlib import Path
        models_dir = Path("data/models")
        if models_dir.exists():
            health["models_loaded"] = True

        # Vérifier RAG
        rag_dir = Path("data/knowledge_base")
        if rag_dir.exists():
            health["rag_available"] = True

        # Vérifier données
        data_dir = Path("data/synthetic_patients.json")
        if data_dir.exists():
            health["data_accessible"] = True

    except Exception as e:
        logger.error(f"Health check failed: {e}")

    return health


def display_system_health():
    """Affiche l'état de santé du système dans la sidebar"""

    health = check_system_health()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏥 État du Système")

    status_icon = {
        True: "✅",
        False: "❌"
    }

    st.sidebar.markdown(f"{status_icon[health['models_loaded']]} Modèles ML")
    st.sidebar.markdown(f"{status_icon[health['rag_available']]} Base RAG")
    st.sidebar.markdown(f"{status_icon[health['data_accessible']]} Données")

    all_healthy = all(health.values())
    if all_healthy:
        st.sidebar.success("Système opérationnel")
    else:
        st.sidebar.warning("Certains composants manquent")

    return all_healthy


def safe_session_state_init(key: str, default_value: Any):
    """
    Initialise une valeur dans session_state si elle n'existe pas

    Args:
        key: Clé dans session_state
        default_value: Valeur par défaut
    """

    if key not in st.session_state:
        st.session_state[key] = default_value
