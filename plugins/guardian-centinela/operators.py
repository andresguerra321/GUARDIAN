"""
GUARDIAN - Centinela Operators
==============================
Operators de FiftyOne para el agente Centinela.
"""

import os
import random

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RunCentinela(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="run_centinela",
            label="GUARDIAN: Ejecutar Centinela",
            description="Analiza frames de dashcam para detectar peligros viales.",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.bool(
            "use_mock",
            label="Usar Mock de Detección",
            description="Simular detecciones sin llamar a la API de IA",
            default=True,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            import sys
            if _PROJECT_ROOT not in sys.path:
                sys.path.insert(0, _PROJECT_ROOT)

            from shared.config import DETECTION_LABELS, SEVERITY_LEVELS

            use_mock = ctx.params.get("use_mock", True)
            dataset = ctx.dataset

            # Intentar importar la función real de IA
            agents_imported = False
            if not use_mock:
                try:
                    from agents.centinela import analyze_frame
                    agents_imported = True
                except ImportError:
                    agents_imported = False

            for sample in dataset.iter_samples(autosave=True, progress=True):
                if use_mock or not agents_imported:
                    # --- Mock ---
                    detections = []
                    for _ in range(random.randint(0, 5)):
                        label = random.choice(DETECTION_LABELS)
                        x = random.uniform(0, 0.8)
                        y = random.uniform(0, 0.8)
                        w = random.uniform(0.05, 1.0 - x)
                        h = random.uniform(0.05, 1.0 - y)
                        detections.append(
                            fo.Detection(
                                label=label,
                                bounding_box=[x, y, w, h],
                                confidence=random.uniform(0.4, 0.99),
                                severity=random.choice(SEVERITY_LEVELS),
                                description=f"{label} detectado",
                            )
                        )
                    sample["detections"] = fo.Detections(detections=detections)
                else:
                    # --- Integración real con agents.centinela ---
                    if sample.filepath:
                        api_dets = analyze_frame(sample.filepath, mock=False)
                        fo_dets = [
                            fo.Detection(
                                label=d.label,
                                bounding_box=d.bounding_box,
                                confidence=d.confidence,
                                severity=d.severity,
                                description=d.description,
                            )
                            for d in api_dets
                        ]
                        sample["detections"] = fo.Detections(detections=fo_dets)

            ctx.trigger("reload_dataset")
            return {"status": "success", "message": "Centinela ejecutado exitosamente"}
        except Exception as e:
            return {"status": "error", "message": f"Error en Centinela: {str(e)}"}
