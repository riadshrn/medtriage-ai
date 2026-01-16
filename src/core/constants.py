from dataclasses import dataclass
from typing import Tuple


@dataclass
class VitalSigns:
    heart_rate: int          # bpm
    respiratory_rate: int    # breaths/min
    spo2: int                # %
    blood_pressure: Tuple[int, int]  # (systolic, diastolic)
    temperature: float       # °C