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

        # Verifier si reentrainement necessaire
        self._check_retraining_trigger()

        return feedback.prediction_id

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


# Instance singleton
_handler = FeedbackHandler()


def get_feedback_handler() -> FeedbackHandler:
    """Retourne l'instance du gestionnaire de feedback."""
    return _handler
