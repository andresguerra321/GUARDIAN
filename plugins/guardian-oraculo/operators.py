"""
GUARDIAN - Oráculo Operators
=============================

Operators de FiftyOne para el agente Oráculo.
"""

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
        inputs.str(
            "msg",
            label="Aviso",
            default="Esto sobreescribirá los scores de riesgo existentes en el dataset.",
            view=types.Warning(label="Ejecutar Oráculo")
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            dataset = ctx.dataset

            for sample in dataset.iter_samples(autosave=True, progress=True):
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
                
                # Determinar nivel de riesgo
                if risk_score < 3.0:
                    risk_level = "low"
                    recommendation = "Continúe ruta normal."
                elif risk_score < 6.0:
                    risk_level = "medium"
                    recommendation = "Precaución: Manténgase alerta al entorno."
                elif risk_score < 8.5:
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

            # Recargar dataset en la UI
            ctx.trigger("reload_dataset")
            return {"status": "success", "message": "Oráculo evaluó los riesgos correctamente"}
        except Exception as e:
            return {"status": "error", "message": f"Aviso de Guardian: {str(e)}"}

def register(p):
    p.register(EvaluateRisk)
