"""
GUARDIAN - Centinela Operators
==============================

Operators de FiftyOne para el agente Centinela.

Operators disponibles:
  - run_centinela: Ejecuta detección sobre un sample individual
  - run_centinela_batch: Ejecuta detección sobre todos los samples del dataset

Estos operators sirven como interfaz entre FiftyOne y la lógica de IA
definida en agents/centinela.py

IMPORTANTE:
  - Los operators deben usar los contratos de shared/contracts.py
  - Las detecciones se almacenan como fo.Detections en el campo "detections"
  - El output debe seguir el formato estándar del equipo

TODO (Rol 2):
  - [ ] Implementar RunCentinela(fo.Operator)
  - [ ] Implementar RunCentinelaBatch(fo.Operator)
  - [ ] Conectar con agents/centinela.py
  - [ ] Registrar operators en __init__.py
"""

# import fiftyone as fo
# import fiftyone.operators as foo
# from agents.centinela import analyze_frame

# Ejemplo de estructura de un Operator:
#
# class RunCentinela(foo.Operator):
#     @property
#     def config(self):
#         return foo.OperatorConfig(
#             name="run_centinela",
#             label="GUARDIAN: Analizar Frame (Centinela)",
#             description="Ejecuta detección de peligros sobre el frame seleccionado",
#         )
#
#     def resolve_input(self, ctx):
#         inputs = foo.types.Object()
#         # Definir inputs del operator
#         return foo.types.Property(inputs)
#
#     def execute(self, ctx):
#         # Llamar a la lógica de IA
#         # sample = ctx.dataset[ctx.current_sample]
#         # detections = analyze_frame(sample.filepath)
#         # sample["detections"] = fo.Detections(detections=[...])
#         # sample.save()
#         pass
