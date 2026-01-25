import json
from pathlib import Path
from typing import List
from src.api.schemas.monitoring import LLMMetrics

class MonitoringService:
    def __init__(self, log_file="data/monitoring_metrics.json"):
        self.log_file = Path(log_file)
        # S'assure que le fichier existe
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w") as f:
                f.write("")

    def log_metric(self, metric: LLMMetrics):
        """Enregistre une métrique réelle dans l'historique (Append)"""
        try:
            with open(self.log_file, "a") as f:
                f.write(metric.json() + "\n")
        except Exception as e:
            print(f"⚠️ Erreur lors du log FinOps: {e}")

    def get_stats(self) -> List[dict]:
        """Récupère l'historique brut pour le dashboard"""
        data = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line))
            except Exception:
                pass
        return data

# Instance singleton
_monitor = MonitoringService()
def get_monitoring_service():
    return _monitor