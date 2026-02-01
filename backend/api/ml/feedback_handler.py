"""
Gestionnaire de feedback pour le reentrainement du modele.

Ce module gere:
- Enregistrement des feedbacks des infirmieres
- Calcul des statistiques de feedback
- Preparation des donnees pour le reentrainement
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import pandas as pd

from api.schemas.feedback import (
    NurseFeedback,
    FeedbackStats,
    FeedbackType,
)

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """Gere le feedback des infirmieres et le reentrainement."""

    # Configuration
    FEEDBACK_DIR = "data/feedback"
    FEEDBACK_FILE = "nurse_feedback.jsonl"

    # Seuils pour declenchement reentrainement
    RETRAINING_THRESHOLD = 100  # Minimum de feedbacks avant reentrainement
    ERROR_RATE_THRESHOLD = 0.15  # Seuil d'erreur pour alerte

    def __init__(self):
        """Initialise le gestionnaire de feedback."""
        self.feedback_dir = Path(self.FEEDBACK_DIR)
        self.feedback_path = self.feedback_dir / self.FEEDBACK_FILE

        # Creer le dossier si necessaire
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def record_feedback(self, feedback: NurseFeedback) -> str:
        """
        Enregistre un feedback.

        Args:
            feedback: Feedback de l'infirmiere

        Returns:
            ID du feedback enregistre
        """
        # Ajouter timestamp
        record = {
            "timestamp": datetime.now().isoformat(),
            **feedback.model_dump(),
        }

        # Ecrire en mode append (JSONL)
        with open(self.feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(
            f"Feedback enregistre: {feedback.prediction_id} "
            f"({feedback.feedback_type.value})"
        )

        # Synchroniser avec history.json
        self._sync_with_history(feedback)

        # Verifier si reentrainement necessaire
        self._check_retraining_trigger()

        return feedback.prediction_id

    def _sync_with_history(self, feedback: NurseFeedback) -> bool:
        """
        Synchronise le feedback avec history.json.

        Met à jour les champs feedback_given, feedback_type et corrected_gravity
        dans l'entrée correspondante de history.json.
        """
        from api.routes.history import load_history, save_history

        try:
            history = load_history()

            for entry in history:
                if entry.get('prediction_id') == feedback.prediction_id:
                    entry['feedback_given'] = True
                    entry['feedback_type'] = feedback.feedback_type.value
                    entry['corrected_gravity'] = feedback.corrected_gravity

                    if save_history(history):
                        logger.info(f"History synchronisé pour {feedback.prediction_id}")
                        return True
                    else:
                        logger.warning(f"Échec de sauvegarde history pour {feedback.prediction_id}")
                        return False

            # Si l'entrée n'existe pas dans history, on la crée
            logger.info(f"Entrée {feedback.prediction_id} non trouvée dans history, création...")
            self._create_history_entry_from_feedback(feedback, history)
            return True

        except Exception as e:
            logger.error(f"Erreur sync history: {e}")
            return False

    def _create_history_entry_from_feedback(self, feedback: NurseFeedback, history: list) -> None:
        """Crée une entrée dans history.json à partir d'un feedback."""
        from api.routes.history import save_history

        # Construire les constantes à partir des features patient
        features = feedback.patient_features or {}
        constantes = {
            "frequence_cardiaque": features.get("frequence_cardiaque"),
            "pression_systolique": features.get("pression_systolique"),
            "pression_diastolique": features.get("pression_diastolique"),
            "frequence_respiratoire": features.get("frequence_respiratoire"),
            "temperature": features.get("temperature"),
            "saturation_oxygene": features.get("saturation_oxygene"),
            "echelle_douleur": features.get("echelle_douleur"),
            "glycemie": features.get("glycemie"),
            "glasgow": features.get("glasgow"),
        }

        entry = {
            "prediction_id": feedback.prediction_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "source": "feedback_import",
            "filename": None,
            "gravity_level": feedback.original_gravity,
            "french_triage_level": feedback.original_french_level,
            "confidence_score": None,
            "orientation": None,
            "delai_prise_en_charge": None,
            "patient_input": None,
            "extracted_data": {
                "age": features.get("age"),
                "sexe": features.get("sexe"),
                "motif_consultation": features.get("motif_consultation"),
                "duree_symptomes": features.get("duree_symptomes"),
                "antecedents": features.get("antecedents", []),
                "traitements": features.get("traitements", []),
                "constantes": constantes,
            },
            "model_version": "imported",
            "ml_available": True,
            "justification": None,
            "red_flags": None,
            "recommendations": None,
            "metrics": None,
            "feedback_given": True,
            "feedback_type": feedback.feedback_type.value,
            "corrected_gravity": feedback.corrected_gravity,
        }

        history.insert(0, entry)
        save_history(history)
        logger.info(f"Nouvelle entrée créée dans history pour {feedback.prediction_id}")

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Charge tous les feedbacks depuis le fichier."""
        if not self.feedback_path.exists():
            return []

        feedback_list = []
        with open(self.feedback_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        feedback_list.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ligne invalide ignoree: {e}")

        return feedback_list

    def get_feedback_count(self) -> int:
        """Retourne le nombre total de feedbacks."""
        return len(self.get_all_feedback())

    def get_stats(
        self,
        since: Optional[datetime] = None
    ) -> FeedbackStats:
        """
        Calcule les statistiques de feedback.

        Args:
            since: Date de debut (optionnel)

        Returns:
            Statistiques agregees
        """
        feedback_list = self.get_all_feedback()

        if not feedback_list:
            return FeedbackStats()

        # Filtrer par date si specifie
        if since:
            feedback_list = [
                f for f in feedback_list
                if datetime.fromisoformat(f["timestamp"]) > since
            ]

        if not feedback_list:
            return FeedbackStats()

        total = len(feedback_list)

        # Compter par type
        correct = sum(1 for f in feedback_list if f["feedback_type"] == FeedbackType.CORRECT.value)
        upgrades = sum(1 for f in feedback_list if f["feedback_type"] == FeedbackType.UPGRADE.value)
        downgrades = sum(1 for f in feedback_list if f["feedback_type"] == FeedbackType.DOWNGRADE.value)
        disagrees = sum(1 for f in feedback_list if f["feedback_type"] == FeedbackType.DISAGREE.value)

        # Stats par niveau de gravite
        by_gravity = self._compute_stats_by_gravity(feedback_list)

        # Periode
        timestamps = [datetime.fromisoformat(f["timestamp"]) for f in feedback_list]

        return FeedbackStats(
            total_predictions=total,
            total_feedback=total,
            accuracy_rate=correct / total if total > 0 else 0,
            upgrade_rate=upgrades / total if total > 0 else 0,
            downgrade_rate=downgrades / total if total > 0 else 0,
            disagree_rate=disagrees / total if total > 0 else 0,
            by_gravity_level=by_gravity,
            period_start=min(timestamps) if timestamps else None,
            period_end=max(timestamps) if timestamps else None,
        )

    def get_feedback_for_retraining(
        self,
        since: Optional[datetime] = None,
        min_samples: int = 50,
    ) -> pd.DataFrame:
        """
        Prepare les donnees de feedback pour reentrainement.

        Seules les corrections (pas les confirmations) sont utilisees.

        Args:
            since: Date de debut (optionnel)
            min_samples: Nombre minimum d'echantillons requis

        Returns:
            DataFrame avec les donnees corrigees
        """
        feedback_list = self.get_all_feedback()

        # Filtrer par date si specifie
        if since:
            feedback_list = [
                f for f in feedback_list
                if datetime.fromisoformat(f["timestamp"]) > since
            ]

        # Garder uniquement les corrections
        correction_types = [
            FeedbackType.UPGRADE.value,
            FeedbackType.DOWNGRADE.value,
            FeedbackType.DISAGREE.value,
        ]
        corrections = [
            f for f in feedback_list
            if f["feedback_type"] in correction_types
        ]

        if len(corrections) < min_samples:
            logger.info(
                f"Pas assez de corrections pour reentrainement: "
                f"{len(corrections)} < {min_samples}"
            )
            return pd.DataFrame()

        # Convertir en format d'entrainement
        rows = []
        for fb in corrections:
            if fb.get("patient_features") and fb.get("corrected_gravity"):
                row = fb["patient_features"].copy()
                row["gravity_level"] = fb["corrected_gravity"]
                rows.append(row)

        if not rows:
            logger.warning("Aucune correction avec features patient valides")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        logger.info(f"Donnees de feedback preparees: {len(df)} echantillons")

        return df

    def _compute_stats_by_gravity(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, int]]:
        """Calcule les stats par niveau de gravite."""
        stats: Dict[str, Dict[str, int]] = {}

        for fb in feedback_list:
            level = fb.get("original_gravity", "UNKNOWN")

            if level not in stats:
                stats[level] = {
                    "total": 0,
                    "correct": 0,
                    "upgraded": 0,
                    "downgraded": 0,
                    "disagreed": 0,
                }

            stats[level]["total"] += 1

            fb_type = fb.get("feedback_type")
            if fb_type == FeedbackType.CORRECT.value:
                stats[level]["correct"] += 1
            elif fb_type == FeedbackType.UPGRADE.value:
                stats[level]["upgraded"] += 1
            elif fb_type == FeedbackType.DOWNGRADE.value:
                stats[level]["downgraded"] += 1
            elif fb_type == FeedbackType.DISAGREE.value:
                stats[level]["disagreed"] += 1

        return stats

    def _check_retraining_trigger(self) -> bool:
        """
        Verifie si un reentrainement devrait etre declenche.

        Returns:
            True si reentrainement recommande
        """
        stats = self.get_stats()

        if stats.total_feedback < self.RETRAINING_THRESHOLD:
            return False

        error_rate = 1 - stats.accuracy_rate
        if error_rate > self.ERROR_RATE_THRESHOLD:
            logger.warning(
                f"Taux d'erreur eleve detecte: {error_rate:.2%} "
                f"(seuil: {self.ERROR_RATE_THRESHOLD:.2%}). "
                f"Reentrainement recommande."
            )
            return True

        return False

    def clear_feedback(self) -> int:
        """
        Efface tous les feedbacks (pour tests).

        Returns:
            Nombre de feedbacks effaces
        """
        count = self.get_feedback_count()

        if self.feedback_path.exists():
            self.feedback_path.unlink()

        logger.info(f"Feedbacks effaces: {count}")
        return count

    def sync_all_feedbacks_to_history(self) -> Dict[str, int]:
        """
        Synchronise tous les feedbacks existants avec history.json.

        Parcourt tous les feedbacks et crée/met à jour les entrées
        correspondantes dans history.json.

        Returns:
            Dictionnaire avec le nombre de feedbacks synchronisés/créés/erreurs
        """
        from api.routes.history import load_history, save_history

        feedback_list = self.get_all_feedback()
        history = load_history()

        # Créer un index des prediction_id existants dans history
        history_index = {entry.get('prediction_id'): i for i, entry in enumerate(history)}

        stats = {"updated": 0, "created": 0, "errors": 0}

        for fb in feedback_list:
            prediction_id = fb.get("prediction_id")
            if not prediction_id:
                stats["errors"] += 1
                continue

            feedback_type = fb.get("feedback_type")
            corrected_gravity = fb.get("corrected_gravity")

            if prediction_id in history_index:
                # Mise à jour de l'entrée existante
                idx = history_index[prediction_id]
                history[idx]["feedback_given"] = True
                history[idx]["feedback_type"] = feedback_type
                history[idx]["corrected_gravity"] = corrected_gravity
                stats["updated"] += 1
            else:
                # Création d'une nouvelle entrée
                features = fb.get("patient_features") or {}
                constantes = {
                    "frequence_cardiaque": features.get("frequence_cardiaque"),
                    "pression_systolique": features.get("pression_systolique"),
                    "pression_diastolique": features.get("pression_diastolique"),
                    "frequence_respiratoire": features.get("frequence_respiratoire"),
                    "temperature": features.get("temperature"),
                    "saturation_oxygene": features.get("saturation_oxygene"),
                    "echelle_douleur": features.get("echelle_douleur"),
                    "glycemie": features.get("glycemie"),
                    "glasgow": features.get("glasgow"),
                }

                entry = {
                    "prediction_id": prediction_id,
                    "timestamp": fb.get("timestamp", datetime.now().isoformat()) + "Z" if not fb.get("timestamp", "").endswith("Z") else fb.get("timestamp"),
                    "source": "feedback_import",
                    "filename": None,
                    "gravity_level": fb.get("original_gravity", "GRIS"),
                    "french_triage_level": fb.get("original_french_level"),
                    "confidence_score": None,
                    "orientation": None,
                    "delai_prise_en_charge": None,
                    "patient_input": None,
                    "extracted_data": {
                        "age": features.get("age"),
                        "sexe": features.get("sexe"),
                        "motif_consultation": features.get("motif_consultation"),
                        "duree_symptomes": features.get("duree_symptomes"),
                        "antecedents": features.get("antecedents", []),
                        "traitements": features.get("traitements", []),
                        "constantes": constantes,
                    },
                    "model_version": "imported",
                    "ml_available": True,
                    "justification": None,
                    "red_flags": None,
                    "recommendations": None,
                    "metrics": None,
                    "feedback_given": True,
                    "feedback_type": feedback_type,
                    "corrected_gravity": corrected_gravity,
                }

                history.append(entry)
                history_index[prediction_id] = len(history) - 1
                stats["created"] += 1

        # Sauvegarder history
        if save_history(history):
            logger.info(f"Synchronisation terminée: {stats}")
        else:
            logger.error("Erreur lors de la sauvegarde de history")
            stats["errors"] += 1

        return stats


# Instance singleton
_handler = FeedbackHandler()


def get_feedback_handler() -> FeedbackHandler:
    """Retourne l'instance du gestionnaire de feedback."""
    return _handler
