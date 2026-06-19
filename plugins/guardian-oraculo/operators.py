"""
GUARDIAN - Oráculo Operators
=============================

Operators de FiftyOne para el agente Oráculo.
"""

import os
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

class EvaluateRisk(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="evaluate_risk",
            label="GUARDIAN: Evaluar Riesgo (Oráculo)",
            description="Evalúa métricas de riesgo basado en las detecciones del Centinela.",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.bool("use_mock", label="Usar Mock", default=False)
        inputs.str(
            "msg",
            label="Aviso",
            default="Esto sobreescribirá los scores de riesgo existentes en el dataset.",
            view=types.Warning(label="Ejecutar Oráculo")
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            use_mock = ctx.params.get("use_mock", False)
            dataset = ctx.dataset
            
            agents_imported = False
            if not use_mock:
                try:
                    from agents.oraculo import evaluate_risk
                    from shared.contracts import Detection
                    agents_imported = True
                except ImportError:
                    agents_imported = False

            for sample in dataset.iter_samples(autosave=True, progress=True):
                if use_mock or not agents_imported:
                    risk_score = 0.0
                    risk_factors = []
                    
                    # Verificar si existen detecciones del centinela de manera segura
                    detections_obj = sample.get("detections", None)
                    if detections_obj is not None and hasattr(detections_obj, "detections"):
                        for det in detections_obj.detections:
                            if det.label == "pedestrian":
                                risk_score += 3.5
                                risk_factors.append("Peatón cercano")
                            elif det.label == "obstacle":
                                risk_score += 2.0
                                risk_factors.append("Obstáculo en la vía")
                            elif det.label == "pothole":
                                risk_score += 1.5
                                risk_factors.append("Bache detectado")
                            elif det.label == "vehicle":
                                risk_score += 1.0
                                risk_factors.append("Vehículo en proximidad")
                            elif det.label == "sign":
                                risk_score += 0.5
                    else:
                        risk_factors.append("No se encontraron detecciones previas válidas.")

                    # Limitar el score a 10.0 (según contrato)
                    risk_score = min(float(risk_score), 10.0)
                    
                    # Determinar nivel de riesgo según RiskScore
                    if risk_score <= 3.0:
                        risk_level = "low"
                        recommendation = "Continúe ruta normal."
                    elif risk_score <= 6.0:
                        risk_level = "medium"
                        recommendation = "Precaución: Manténgase alerta al entorno."
                    elif risk_score <= 8.0:
                        risk_level = "high"
                        recommendation = "Alerta: Reduzca la velocidad inmediatamente."
                    else:
                        risk_level = "critical"
                        recommendation = "¡PELIGRO! Detenga el vehículo de inmediato o evada el peligro."

                    # Guardar en contratos de datos estrictos
                    sample["risk_score"] = float(risk_score)
                    sample["risk_level"] = str(risk_level)
                    sample["risk_factors"] = risk_factors  # list de str
                    sample["recommendation"] = str(recommendation)
                    sample["historical_incidents"] = 0
                else:
                    # Integración Real
                    dets_contract = []
                    detections_obj = sample.get("detections", None)
                    if detections_obj is not None and hasattr(detections_obj, "detections"):
                        for d in detections_obj.detections:
                            dets_contract.append(Detection(
                                label=d.label,
                                confidence=getattr(d, "confidence", 1.0),
                                bounding_box=d.bounding_box,
                                severity=getattr(d, "severity", "medium"),
                                description=getattr(d, "description", "")
                            ))
                    
                    # Evaluate risk con API
                    risk_obj = evaluate_risk(dets_contract, metadata={})
                    sample["risk_score"] = float(risk_obj.score)
                    sample["risk_level"] = str(risk_obj.level)
                    sample["risk_factors"] = risk_obj.factors
                    sample["recommendation"] = str(risk_obj.recommendation)
                    sample["historical_incidents"] = risk_obj.historical_incidents

            # Recargar dataset en la UI
            ctx.trigger("reload_dataset")
            return {"status": "success", "message": "Oráculo evaluó los riesgos correctamente"}
        except Exception as e:
            return {"status": "error", "message": f"Aviso de Guardian: {str(e)}"}


