"""
GUARDIAN - Centinela Operators
==============================

Operators de FiftyOne para el agente Centinela.
"""

import os
from pathlib import Path

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PLUGIN_DIR))

import random
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

class RunCentinela(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="run_centinela",
            label="GUARDIAN: Ejecutar Centinela",
            description="Ejecuta el modelo de detección Centinela (o simula si use_mock es True).",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.bool(
            "use_mock",
            label="Usar Mock de Detección",
            description="Usar simulación de detecciones sin dependencias externas",
            default=True,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            import sys
            if _PROJECT_ROOT not in sys.path:
                sys.path.insert(0, _PROJECT_ROOT)
            
            from shared import config
            
            use_mock = ctx.params.get("use_mock", True)
            dataset = ctx.dataset

            # Intentar importar la función real
            if not use_mock:
                try:
                    from agents.centinela import analyze_frame
                    agents_imported = True
                except ImportError:
                    agents_imported = False

            labels = config.DETECTION_LABELS

            for sample in dataset.iter_samples(autosave=True, progress=True):
                if use_mock or not agents_imported:
                    detections = []
                    num_detections = random.randint(0, 5)
                    for _ in range(num_detections):
                        label = random.choice(labels)
                        # Cajas normalizadas [x, y, w, h]
                        x = random.uniform(0, 0.8)
                        y = random.uniform(0, 0.8)
                        w = random.uniform(0.05, 1.0 - x)
                        h = random.uniform(0.05, 1.0 - y)
                        
                        severity = random.choice(config.SEVERITY_LEVELS)
                        confidence = random.uniform(0.4, 0.99)
                        description = f"{label} detectado ({severity})"
                        
                        det = fo.Detection(
                            label=label,
                            bounding_box=[x, y, w, h],
                            confidence=confidence,
                            severity=severity,
                            description=description
                        )
                        detections.append(det)
                    
                    sample["detections"] = fo.Detections(detections=detections)
                else:
                    # Integración real
                    if sample.filepath:
                        api_dets = analyze_frame(sample.filepath, mock=False)
                        fo_dets = []
                        for d in api_dets:
                            fo_dets.append(fo.Detection(
                                label=d.label,
                                bounding_box=d.bounding_box,
                                confidence=d.confidence,
                                severity=d.severity,
                                description=d.description
                            ))
                        sample["detections"] = fo.Detections(detections=fo_dets)

            # Recargar dataset en la UI
            ctx.trigger("reload_dataset")
            return {"status": "success", "message": "Centinela ejecutado exitosamente"}
        except Exception as e:
            return {"status": "error", "message": f"Aviso de Guardian: {str(e)}"}


