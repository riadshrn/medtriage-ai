from dataclasses import dataclass
from typing import List

from .constants import VitalSigns
from .severity import SeverityLevel


@dataclass
class Patient:
    first_name: str
    last_name: str
    symptoms: List[str]
    vital_signs: VitalSigns
    severity: SeverityLevel | None = None