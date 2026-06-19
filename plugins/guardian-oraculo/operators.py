"""
GUARDIAN - Oráculo Operators
=============================

Operators de FiftyOne para el agente Oráculo.

Operators disponibles:
  - evaluate_risk: Evalúa riesgo de un sample individual
  - evaluate_risk_batch: Evalúa riesgo de todos los samples

El Oráculo toma las detecciones del Centinela + metadata del sample
y genera:
  - risk_score (float 0-10)
  - risk_factors (list[str])
  - recommendation (str)

IMPORTANTE:
  - Requiere que el Centinela haya corrido primero (campo "detections" debe existir)
  - El output se almacena en campos "risk_score", "risk_factors", "recommendation"
  - Usa los contratos de shared/contracts.py

TODO (Rol 2):
  - [ ] Implementar EvaluateRisk(fo.Operator)
  - [ ] Implementar EvaluateRiskBatch(fo.Operator)
  - [ ] Conectar con agents/oraculo.py
"""

# import fiftyone as fo
# import fiftyone.operators as foo
# from agents.oraculo import evaluate_risk
