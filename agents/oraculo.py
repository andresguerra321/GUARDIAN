"""
GUARDIAN - Agente Oráculo (Lógica de IA)
=========================================

Este módulo evalúa el riesgo de una escena/zona combinando:
  - Detecciones del Centinela
  - Metadata del sample (GPS, clima, hora)
  - Historial de accidentes (si disponible)

Interfaz principal:
  - evaluate_risk(detections, metadata) -> RiskScore

TODO (Rol 4):
  - [ ] Implementar evaluate_risk() con lógica de scoring
  - [ ] Implementar modo mock para desarrollo
  - [ ] Definir pesos de factores de riesgo
  - [ ] Integrar con Gemini para análisis semántico del contexto
"""

from shared.contracts import Detection, RiskScore


def evaluate_risk(
    detections: list[Detection],
    metadata: dict = None,
    mock: bool = False,
) -> RiskScore:
    """
    Evalúa el riesgo de una escena basándose en detecciones y contexto.

    Args:
        detections: Lista de detecciones del Centinela
        metadata: Metadata del sample (gps, clima, hora, conductor, etc.)
        mock: Si True, devuelve un score mock

    Returns:
        RiskScore con score, factores y recomendación
    """
    if mock:
        return _mock_risk_score()

    # TODO: Implementar evaluación de riesgo real
    # Factores a considerar:
    # - Número y severidad de detecciones
    # - Condiciones climáticas
    # - Hora del día (noche = más riesgo)
    # - Historial de accidentes en la zona
    # - Horas de conducción del conductor

    raise NotImplementedError("Implementar evaluación de riesgo - Rol 4")


def _mock_risk_score() -> RiskScore:
    """Devuelve un score mock para desarrollo."""
    return RiskScore(
        score=7.3,
        factors=["pedestrian_zone", "rain", "night"],
        recommendation="Reducir velocidad a 40km/h. Zona de alta actividad peatonal con lluvia.",
        historical_incidents=5,
    )
