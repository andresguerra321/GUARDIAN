"""
GUARDIAN - Agente Copiloto (Lógica de IA)
==========================================

Asistente conversacional que interactúa con el conductor y genera
briefings de seguridad basados en el contexto de detecciones y riesgo.

Interfaz:
  - ask(message, context) -> str
  - generate_briefing(context) -> str
"""

import os
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

from shared.contracts import Detection, RiskScore

load_dotenv()
logger = logging.getLogger(__name__)

# === Cliente Gemini ===
_client = None


def _get_client():
    """Obtiene o crea el cliente de Gemini (singleton)."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "PEGA_TU_KEY_AQUI":
            raise ValueError("GEMINI_API_KEY no configurada.")
        _client = genai.Client(api_key=api_key)
    return _client


def _load_system_prompt() -> str:
    """Carga el system prompt del Copiloto."""
    prompt_path = Path(__file__).parent / "prompts" / "copiloto_system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "Eres un copiloto de seguridad vial. Responde de forma breve y accionable."


def _build_context(
    detections: list[Detection] = None,
    risk_score: RiskScore = None,
    driver_info: dict = None,
    route_info: dict = None,
) -> str:
    """Construye el contexto como texto para inyectar en el prompt."""
    parts = []

    if route_info:
        parts.append(
            f"RUTA: {route_info.get('origin', '?')} → {route_info.get('destination', '?')}"
        )

    if driver_info:
        parts.append(f"CONDUCTOR: {driver_info.get('name', 'Desconocido')}")
        hours = driver_info.get("hours_driving", 0)
        if hours > 0:
            parts.append(f"HORAS CONDUCIENDO: {hours:.1f}h continuas")
        status = driver_info.get("status", "active")
        parts.append(f"ESTADO: {status}")

    if risk_score:
        parts.append(
            f"RIESGO ACTUAL: {risk_score.score}/10 ({risk_score.level})"
        )
        if risk_score.factors:
            parts.append(f"FACTORES: {', '.join(risk_score.factors)}")
        if risk_score.recommendation:
            parts.append(f"RECOMENDACIÓN ORÁCULO: {risk_score.recommendation}")

    if detections:
        parts.append(f"DETECCIONES ACTIVAS ({len(detections)}):")
        for d in detections:
            parts.append(
                f"  - [{d.severity.upper()}] {d.label}: {d.description} "
                f"(confianza: {d.confidence:.0%})"
            )

    if not parts:
        parts.append("Sin contexto adicional disponible.")

    return "\n".join(parts)


# === Función principal: Preguntar al Copiloto ===
def ask(
    message: str,
    detections: list[Detection] = None,
    risk_score: RiskScore = None,
    driver_info: dict = None,
    route_info: dict = None,
    mock: bool = False,
) -> str:
    """
    Envía un mensaje al Copiloto y recibe respuesta contextualizada.

    Args:
        message: Mensaje del conductor o del sistema
        detections: Detecciones activas del Centinela
        risk_score: Score de riesgo actual del Oráculo
        driver_info: Info del conductor
        route_info: Info de la ruta
        mock: Si True, devuelve respuesta mock

    Returns:
        Respuesta del Copiloto en lenguaje natural
    """
    if mock:
        return _mock_response(message)

    try:
        client = _get_client()
        system_prompt = _load_system_prompt()
        context = _build_context(detections, risk_score, driver_info, route_info)

        full_prompt = f"{system_prompt}\n\n--- CONTEXTO ACTUAL ---\n{context}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part.from_text(text=message),
                    ],
                )
            ],
            config=genai_types.GenerateContentConfig(
                system_instruction=full_prompt,
                temperature=0.7,
                max_output_tokens=300,
            ),
        )

        answer = response.text.strip()
        logger.info(f"Copiloto respondió: {answer[:100]}...")
        return answer

    except Exception as e:
        logger.error(f"Error en Copiloto: {e}")
        return _mock_response(message)


# === Función: Generar Briefing de Ruta ===
def generate_briefing(
    detections: list[Detection] = None,
    risk_score: RiskScore = None,
    route_info: dict = None,
    driver_info: dict = None,
    scene_summaries: list[str] = None,
    mock: bool = False,
) -> str:
    """
    Genera un briefing narrativo de seguridad para la ruta.

    Args:
        detections: Todas las detecciones de la ruta
        risk_score: Score de riesgo promedio
        route_info: Info de la ruta (origin, destination)
        driver_info: Info del conductor
        scene_summaries: Resúmenes de escenas analizadas
        mock: Si True, devuelve briefing mock

    Returns:
        Briefing narrativo en lenguaje natural
    """
    if mock:
        return _mock_briefing()

    try:
        client = _get_client()
        context = _build_context(detections, risk_score, driver_info, route_info)

        # Info extra de escenas
        scenes_text = ""
        if scene_summaries:
            scenes_text = "\n\nRESÚMENES DE ESCENAS ANALIZADAS:\n"
            for i, s in enumerate(scene_summaries, 1):
                scenes_text += f"  Escena {i}: {s}\n"

        prompt = (
            "Genera un BRIEFING DE SEGURIDAD breve para el conductor. "
            "Debe ser profesional, conciso, y accionable. "
            "Formato:\n"
            "1. Línea de riesgo general (emoji + nivel)\n"
            "2. Puntos críticos encontrados (máx 3)\n"
            "3. Recomendaciones concretas (máx 3)\n"
            "4. Una frase de cierre motivacional\n\n"
            f"CONTEXTO:\n{context}{scenes_text}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=genai_types.GenerateContentConfig(
                system_instruction=_load_system_prompt(),
                temperature=0.5,
                max_output_tokens=500,
            ),
        )

        briefing = response.text.strip()
        logger.info(f"Briefing generado ({len(briefing)} chars)")
        return briefing

    except Exception as e:
        logger.error(f"Error generando briefing: {e}")
        return _mock_briefing()


# === Mocks ===
def _mock_response(message: str) -> str:
    """Respuesta mock contextualizada."""
    message_lower = message.lower()

    if any(w in message_lower for w in ["cansado", "sueño", "fatiga", "dormir"]):
        return (
            "⚠️ Entiendo que estás cansado. Tu seguridad es lo primero. "
            "Hay un punto de descanso en 12 km (estación El Roble). "
            "Te recomiendo parar ahí al menos 20 minutos. ¿Te parece?"
        )

    if any(w in message_lower for w in ["clima", "lluvia", "tiempo", "llueve"]):
        return (
            "🌧️ Según los datos, hay lluvia moderada en los próximos 15 km. "
            "Reduce velocidad a 50km/h y enciende luces. "
            "La vía se despeja después del km 85."
        )

    if any(w in message_lower for w in ["ruta", "camino", "alternativa", "desvío"]):
        return (
            "🗺️ Tu ruta actual Bogotá → Bucaramanga tiene riesgo ALTO en el tramo "
            "km 45-78. La variante por Barbosa añade 25 min pero reduce riesgo un 60%. "
            "¿Quieres que recalcule?"
        )

    if any(w in message_lower for w in ["cómo", "estado", "reporte", "situación"]):
        return (
            "📊 Situación actual:\n"
            "• Riesgo: MODERADO (5.2/10)\n"
            "• 3 detecciones activas (1 peatón, 2 vehículos)\n"
            "• Clima: nublado, sin lluvia\n"
            "• Llevas 2.5h conduciendo, todo dentro de lo normal.\n"
            "Sigues bien, mantén la atención. 👍"
        )

    return (
        f"Recibido. Basado en el análisis actual del Centinela y el Oráculo, "
        f"las condiciones de tu ruta son estables. "
        f"Mantén velocidad y distancia de seguridad. "
        f"Estoy aquí si necesitas algo. 🛡️"
    )


def _mock_briefing() -> str:
    """Briefing mock para desarrollo."""
    return (
        "🛡️ BRIEFING GUARDIAN — Ruta Bogotá → Bucaramanga\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ Riesgo general: ALTO (7.3/10)\n\n"
        "📍 Puntos críticos detectados:\n"
        "  1. Km 45-78: Lluvia intensa + historial de 5 accidentes previos\n"
        "  2. Km 112: Zona escolar con peatones detectados\n"
        "  3. Km 180-195: Curvas cerradas, superficie mojada\n\n"
        "✅ Recomendaciones:\n"
        "  • Reducir velocidad a 40km/h en tramos marcados\n"
        "  • Parada de descanso en km 150 (llevas 3.5h conduciendo)\n"
        "  • Mantener luces encendidas por condiciones de lluvia\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Buen viaje. GUARDIAN te acompaña. 🚛"
    )


# === Test rápido ===
if __name__ == "__main__":
    from agents.centinela import _mock_detections
    from agents.oraculo import _mock_risk_score

    print("🛡️ GUARDIAN — Test del Agente Copiloto")
    print("=" * 50)

    detections = _mock_detections()
    risk = _mock_risk_score()
    driver = {"name": "Carlos Pérez", "hours_driving": 3.5, "status": "active"}
    route = {"origin": "Bogotá", "destination": "Bucaramanga"}

    # Test mock responses
    test_messages = [
        "¿Cómo está la situación?",
        "Estoy muy cansado",
        "¿Cómo está el clima adelante?",
        "¿Hay alguna ruta alternativa?",
        "Todo tranquilo por ahora",
    ]

    print("\n📋 Test de respuestas (MOCK):")
    for msg in test_messages:
        print(f"\n  👤 Conductor: {msg}")
        response = ask(msg, detections, risk, driver, route, mock=True)
        print(f"  🤖 Copiloto: {response}")

    # Test briefing
    print("\n\n📋 Test de Briefing (MOCK):")
    print(generate_briefing(mock=True))

    # Test con Gemini real
    print("\n\n📋 Test con Gemini (REAL):")
    try:
        real_response = ask(
            "¿Cómo está la situación de la ruta?",
            detections, risk, driver, route,
            mock=False,
        )
        print(f"  🤖 Copiloto: {real_response}")

        print("\n  Briefing real:")
        real_briefing = generate_briefing(
            detections, risk, route, driver,
            scene_summaries=["Tráfico moderado con peatón cruzando", "Lluvia en la vía"],
            mock=False,
        )
        print(f"  {real_briefing}")
    except Exception as e:
        print(f"  ⚠️ Gemini no disponible: {e}")
        print("  (Esto es normal si no configuraste GEMINI_API_KEY)")
