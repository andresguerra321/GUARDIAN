"""
GUARDIAN - Copiloto Operators
==============================

Operators de FiftyOne para el agente Copiloto.

Operators disponibles:
  - ask_copiloto: Envía un mensaje/pregunta al Copiloto y recibe respuesta
  - generate_briefing: Genera un briefing narrativo de riesgo para la ruta/dataset actual

El Copiloto recibe como contexto:
  - Detecciones activas (del Centinela)
  - Score de riesgo (del Oráculo)
  - Metadata del vehículo/conductor
  - Historial de alertas

Y genera:
  - Respuestas conversacionales en lenguaje natural
  - Briefings de ruta con recomendaciones

TODO (Rol 4 + Rol 2):
  - [ ] Implementar AskCopiloto(fo.Operator) con input de texto
  - [ ] Implementar GenerateBriefing(fo.Operator)
  - [ ] Conectar con agents/copiloto.py
  - [ ] Mostrar output en el Panel Dashboard
"""

# import fiftyone as fo
# import fiftyone.operators as foo
# from agents.copiloto import ask, generate_briefing
