"""
GUARDIAN - Contratos de Datos
==============================

Este módulo define las estructuras de datos compartidas por TODO el equipo.

REGLAS:
  - Solo Rol 5 modifica este archivo
  - Todos los demás roles IMPORTAN de aquí, no inventan formatos propios
  - Si necesitas un campo nuevo, pídelo al Rol 5
  - Todos los campos usan snake_case
  - Todos los timestamps en ISO 8601
  - Todos los scores: 0-10 (riesgo) o 0-1 (confianza/fatiga)
  - IDs con prefijos: VH-, DR-, AL-, EV-
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid
from datetime import datetime


# === DETECCIÓN (output del Centinela) ===

@dataclass
class Detection:
    """Una detección individual en un frame de dashcam."""
    label: str                    # "vehicle", "pedestrian", "obstacle", "sign", "pothole"
    confidence: float             # 0.0 a 1.0
    bounding_box: list[float]     # [x, y, w, h] normalizado (formato FiftyOne)
    severity: str                 # "low", "medium", "high", "critical"
    description: str              # "Peatón cruzando fuera de paso cebra a 30m"


# === ALERTA (generada por Oráculo) ===

@dataclass
class Alert:
    """Una alerta de seguridad generada por el sistema."""
    type: str                     # "hazard", "fatigue", "compliance", "weather"
    severity: str                 # "info", "warning", "danger", "emergency"
    title: str                    # "Peatón en vía"
    description: str              # Descripción legible
    vehicle_id: str               # "VH-001"
    risk_score: float             # 0.0 a 10.0
    id: str = field(default_factory=lambda: f"AL-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    location: Optional[dict] = None       # {"lat": 4.7110, "lon": -74.0721}
    detections: list[Detection] = field(default_factory=list)


# === VEHÍCULO ===

@dataclass
class Vehicle:
    """Un vehículo de la flota."""
    id: str                       # "VH-001"
    plate: str                    # "ABC-123"
    type: str                     # "truck", "bus", "van"
    driver_id: str                # "DR-001"
    status: str = "active"        # "active", "alert", "emergency", "resting"
    location: Optional[dict] = None       # {"lat": 4.7110, "lon": -74.0721}
    route: Optional[dict] = None          # {"origin": "Bogotá", "destination": "Bucaramanga"}
    current_risk: float = 0.0     # 0.0 a 10.0


# === CONDUCTOR ===

@dataclass
class Driver:
    """Un conductor de la flota."""
    id: str                       # "DR-001"
    name: str
    hours_driving: float = 0.0    # Horas continuas al volante
    fatigue_score: float = 0.0    # 0.0 a 1.0
    total_alerts: int = 0
    status: str = "active"        # "active", "fatigued", "resting"


# === EVENTO (registro histórico) ===

@dataclass
class Event:
    """Un evento registrado en el sistema."""
    type: str                     # "detection", "alert", "copilot_message", "risk_change"
    vehicle_id: str
    data: dict = field(default_factory=dict)  # Payload flexible del evento
    id: str = field(default_factory=lambda: f"EV-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# === SCORE DE RIESGO (output del Oráculo) ===

@dataclass
class RiskScore:
    """Score de riesgo calculado por el Oráculo."""
    score: float                  # 0.0 a 10.0
    factors: list[str]            # ["rain", "curve", "pedestrian_zone", "night"]
    recommendation: str           # "Reducir velocidad a 40km/h"
    historical_incidents: int = 0 # Accidentes previos en esta zona

    @property
    def level(self) -> str:
        """Nivel de riesgo legible."""
        if self.score <= 3:
            return "low"
        elif self.score <= 6:
            return "medium"
        elif self.score <= 8:
            return "high"
        else:
            return "critical"
