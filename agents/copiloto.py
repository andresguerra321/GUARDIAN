"""
GUARDIAN - Agente Copiloto (Lógica de IA)
==========================================

Este módulo implementa el asistente conversacional que interactúa
con el conductor en lenguaje natural.

Interfaz principal:
  - ask(message, context) -> str
  - generate_briefing(context) -> str

El Copiloto recibe contexto de:
  - Detecciones activas del Centinela
  - Score de riesgo del Oráculo
  - Metadata del vehículo/conductor/ruta
  - Historial de alertas

TODO (Rol 4):
  - [ ] Implementar ask() con Gemini API
  - [ ] Implementar generate_briefing() con Gemini API
  - [ ] Escribir system prompt detallado en prompts/copiloto_system.md
  - [ ] Implementar modo mock
  - [ ] Manejar contexto de conversación (historial)
"""

import os
from shared.contracts import Detection, RiskScore


def ask(
    message: str,
    detections: list[Detection] = None,
    risk_score: RiskScore = None,
    driver_info: dict = None,
    mock: bool = False,
) -> str:
    """
    Envía un mensaje al Copiloto y recibe una respuesta contextualizada.

    Args:
        message: Mensaje del conductor o del sistema
        detections: Detecciones activas del Centinela
        risk_score: Score de riesgo actual del Oráculo
        driver_info: Info del conductor (horas conduciendo, etc.)
        mock: Si True, devuelve respuesta mock

    Returns:
        Respuesta del Copiloto en lenguaje natural
    """
    if mock:
        return _mock_response(message)

    # TODO: Implementar con Gemini API
    # from google import genai
    # client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    #
    # system_prompt = _load_system_prompt()
    # context = _build_context(detections, risk_score, driver_info)
    #
    # response = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=[system_prompt + context, message],
    # )
    # return response.text

    raise NotImplementedError("Implementar Copiloto con Gemini - Rol 4")


def generate_briefing(
    detections: list[Detection] = None,
    risk_score: RiskScore = None,
    route_info: dict = None,
    mock: bool = False,
) -> str:
    """
    Genera un briefing narrativo de riesgo para la ruta actual.

    Args:
        detections: Todas las detecciones de la ruta
        risk_score: Score de riesgo promedio
        route_info: Info de la ruta (origen, destino, waypoints)
        mock: Si True, devuelve briefing mock

    Returns:
        Briefing narrativo en lenguaje natural
    """
    if mock:
        return _mock_briefing()

    # TODO: Implementar con Gemini API
    raise NotImplementedError("Implementar briefing con Gemini - Rol 4")


def _mock_response(message: str) -> str:
    """Respuesta mock del Copiloto."""
    return (
        f'Entendido. Recibí tu mensaje: "{message}". '
        "Según las detecciones del Centinela, hay actividad peatonal "
        "en los próximos 500m. El Oráculo indica riesgo ALTO (7.3/10). "
        "Te recomiendo reducir velocidad a 40km/h y mantener distancia."
    )


def _mock_briefing() -> str:
    """Briefing mock para desarrollo."""
    return (
        "🛡️ BRIEFING GUARDIAN - Ruta Bogotá → Bucaramanga\n\n"
        "Riesgo general: ALTO (7.3/10)\n\n"
        "⚠️ Puntos críticos:\n"
        "- Km 45-78: Lluvia intensa + historial de 5 accidentes\n"
        "- Km 112: Zona escolar activa en horario pico\n"
        "- Km 180-195: Curvas cerradas con visibilidad reducida\n\n"
        "✅ Recomendaciones:\n"
        "- Reducir velocidad en tramos marcados\n"
        "- Parada de descanso sugerida en km 150 (llevas 3.5h conduciendo)\n"
        "- Mantener luces encendidas por condiciones de lluvia\n\n"
        "Buen viaje. GUARDIAN te acompaña. 🚛"
    )
