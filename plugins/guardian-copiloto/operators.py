"""
GUARDIAN - Copiloto Operators
=============================

Operators de FiftyOne para el agente Copiloto (LLM interactivo y Briefing).
"""

import os
from pathlib import Path

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PLUGIN_DIR))


import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

class AskCopiloto(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="ask_copiloto",
            label="GUARDIAN: Consultar al Copiloto",
            description="Consulta interactiva con el asistente LLM sobre el contexto actual.",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "user_message",
            label="Tu pregunta",
            description="Escribe aquí tu consulta para el Copiloto.",
            required=True
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            import sys
            if _PROJECT_ROOT not in sys.path:
                sys.path.insert(0, _PROJECT_ROOT)
                
            user_message = ctx.params.get("user_message", "")
            
            # Bloque try-except de control para integración futura
            copiloto_imported = False
            try:
                from agents.copiloto import ask
                copiloto_imported = True
            except ImportError:
                copiloto_imported = False

            if not copiloto_imported:
                # Mock de respuesta
                response = (
                    f"🤖 [Mock Copiloto]: He analizado tu pregunta '{user_message}'. "
                    "Actualmente estoy operando en modo simulado, pero puedo confirmar "
                    "que el sistema GUARDIAN está procesando las telemetrías de esta sesión."
                )
            else:
                # Real API
                response = ask(user_message, mock=False)
                
            return {"status": "success", "message": "Copiloto respondió exitosamente", "response": response}
        except Exception as e:
            return {"status": "error", "message": f"Aviso de Guardian: {str(e)}"}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "response",
            label="Respuesta del Copiloto",
            view=types.Notice()
        )
        return types.Property(outputs)


class GenerateBriefing(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="generate_briefing",
            label="GUARDIAN: Generar Reporte de Ruta",
            description="Genera un resumen analítico basado en los scores de riesgo actuales.",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "info",
            label="Aviso",
            default="Se iterará sobre el dataset para compilar un reporte narrativo de los riesgos.",
            view=types.Warning(label="Generar Reporte")
        )
        return types.Property(inputs)

    def execute(self, ctx):
        try:
            import sys
            if _PROJECT_ROOT not in sys.path:
                sys.path.insert(0, _PROJECT_ROOT)
                
            dataset = ctx.dataset
            
            total_samples = 0
            risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            avg_score = 0.0
            
            # Análisis del dataset actual
            for sample in dataset.iter_samples(progress=True):
                total_samples += 1
                if "risk_level" in sample and sample["risk_level"] is not None:
                    r_level = str(sample["risk_level"]).lower()
                    if r_level in risk_counts:
                        risk_counts[r_level] += 1
                
                if "risk_score" in sample and sample["risk_score"] is not None:
                    avg_score += float(sample["risk_score"])
                    
            if total_samples > 0:
                avg_score /= total_samples
            else:
                avg_score = 0.0
                
            # Bloque try-except de control para integración futura
            copiloto_imported = False
            try:
                from agents.copiloto import generate_briefing
                from shared.contracts import RiskScore
                copiloto_imported = True
            except ImportError:
                copiloto_imported = False
                
            if not copiloto_imported:
                # Generación de Briefing Mock
                briefing = (
                    f"📋 **REPORTE DE RUTA GUARDIAN**\n\n"
                    f"- Muestras procesadas: {total_samples}\n"
                    f"- Riesgo Promedio: {avg_score:.2f}/10.0\n"
                    f"- Alertas Críticas: {risk_counts.get('critical', 0)}\n"
                    f"- Alertas Altas: {risk_counts.get('high', 0)}\n\n"
                )
                
                if risk_counts.get("critical", 0) > 0:
                    briefing += "⚠️ **ALERTA ROJA:** Ruta inestable. Se detectaron incidentes críticos severos. Requiere revisión humana inmediata."
                elif risk_counts.get("high", 0) > 0:
                    briefing += "⚠️ **ADVERTENCIA:** Se registraron factores de riesgo altos. Se recomienda cautela en los tramos identificados."
                else:
                    briefing += "✅ **RUTA ESTABLE:** Operaciones normales. Las métricas de riesgo se mantienen en niveles tolerables."
            else:
                # Real API
                rs = RiskScore(score=avg_score, factors=["Resumen general"], recommendation="Verificar el tablero.", historical_incidents=0)
                briefing = generate_briefing(
                    detections=[],
                    risk_score=rs,
                    route_info={"origin": "N/A", "destination": "N/A"},
                    driver_info={"name": "Flota", "status": "active"},
                    mock=False
                )

            return {"status": "success", "message": "Briefing generado exitosamente", "briefing": briefing}
        except Exception as e:
            return {"status": "error", "message": f"Aviso de Guardian: {str(e)}"}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "briefing",
            label="Reporte de Ruta",
            view=types.Notice()
        )
        return types.Property(outputs)
