"""
GUARDIAN - Agente Oráculo (Lógica de IA)
=========================================

Evalúa el riesgo de una escena/zona combinando:
  - Detecciones del Centinela
  - Metadata del contexto (GPS, clima, hora)
  - Factores acumulativos

Interfaz:
  - evaluate_risk(detections, metadata) -> RiskScore
  - evaluate_risk_with_ai(detections, metadata) -> RiskScore  (usa Gemini)
"""

import os
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from shared.contracts import Detection, RiskScore

load_dotenv()
logger = logging.getLogger(__name__)


# === Pesos de factores de riesgo ===
SEVERITY_WEIGHTS = {
    "critical": 3.0,
    "high": 2.0,
    "medium": 1.0,
    "low": 0.3,
}

LABEL_RISK_WEIGHTS = {
    "pedestrian": 2.5,
    "obstacle": 2.0,
    "pothole": 1.5,
    "weather_hazard": 2.0,
    "road_condition": 1.2,
    "vehicle": 0.5,
    "sign": 0.2,
}

WEATHER_RISK = {
    "rain": 2.0,
    "fog": 2.5,
    "snow": 3.0,
    "storm": 3.5,
    "cloudy": 0.5,
    "sunny": 0.0,
    "clear": 0.0,
}

TIME_RISK = {
    "night": 1.5,
    "dawn": 1.0,
    "dusk": 1.0,
    "morning": 0.0,
    "afternoon": 0.0,
}


def evaluate_risk(
    detections: list[Detection],
    metadata: dict = None,
    mock: bool = False,
) -> RiskScore:
    """
    Evalúa el riesgo combinando detecciones + contexto con reglas ponderadas.

    Args:
        detections: Lista de detecciones del Centinela
        metadata: dict con keys opcionales: weather, time_of_day, 
                  hours_driving, speed, zone_type
        mock: Si True, devuelve score mock

    Returns:
        RiskScore con score (0-10), factors, recommendation
    """
    if mock:
        return _mock_risk_score()

    if metadata is None:
        metadata = {}

    score = 0.0
    factors = []

    # --- Factor 1: Detecciones por severidad y tipo ---
    if detections:
        for det in detections:
            # Peso por severidad
            sev_weight = SEVERITY_WEIGHTS.get(det.severity, 1.0)
            # Peso por tipo de objeto
            label_weight = LABEL_RISK_WEIGHTS.get(det.label, 0.5)
            # Contribución al score
            contribution = sev_weight * label_weight * det.confidence * 0.5
            score += contribution

        # Factores por tipo de detección
        labels_found = set(d.label for d in detections)
        if "pedestrian" in labels_found:
            factors.append("pedestrian_zone")
        if "obstacle" in labels_found:
            factors.append("obstacle_detected")
        if "pothole" in labels_found:
            factors.append("road_damage")
        if "weather_hazard" in labels_found:
            factors.append("weather_hazard_visible")

        # Detecciones de alta severidad
        high_count = sum(1 for d in detections if d.severity in ("high", "critical"))
        if high_count > 0:
            factors.append(f"{high_count}_high_severity_detections")

        # Densidad de objetos (muchos objetos = más riesgo)
        if len(detections) >= 5:
            score += 1.0
            factors.append("high_object_density")

    # --- Factor 2: Clima ---
    weather = metadata.get("weather", "").lower()
    weather_score = WEATHER_RISK.get(weather, 0.0)
    if weather_score > 0:
        score += weather_score
        factors.append(weather)

    # --- Factor 3: Hora del día ---
    time_of_day = metadata.get("time_of_day", "").lower()
    time_score = TIME_RISK.get(time_of_day, 0.0)
    if time_score > 0:
        score += time_score
        factors.append(f"driving_at_{time_of_day}")

    # --- Factor 4: Fatiga del conductor ---
    hours_driving = metadata.get("hours_driving", 0)
    if hours_driving >= 4:
        fatigue_score = min((hours_driving - 3) * 0.8, 3.0)
        score += fatigue_score
        factors.append("driver_fatigue")

    # --- Factor 5: Velocidad excesiva ---
    speed = metadata.get("speed", 0)
    speed_limit = metadata.get("speed_limit", 80)
    if speed > 0 and speed > speed_limit:
        excess = (speed - speed_limit) / speed_limit
        score += min(excess * 4.0, 2.0)
        factors.append("speeding")

    # --- Factor 6: Zona especial ---
    zone_type = metadata.get("zone_type", "").lower()
    if zone_type in ("school", "hospital", "residential"):
        score += 1.5
        factors.append(f"{zone_type}_zone")

    # --- Factor 7: Historial de incidentes ---
    historical = metadata.get("historical_incidents", 0)
    if historical > 0:
        score += min(historical * 0.3, 1.5)
        factors.append("historical_incidents")

    # Cap en 10
    score = round(min(score, 10.0), 1)

    # Generar recomendación
    recommendation = _generate_recommendation(score, factors, metadata)

    return RiskScore(
        score=score,
        factors=factors,
        recommendation=recommendation,
        historical_incidents=historical,
    )


def _generate_recommendation(score: float, factors: list[str], metadata: dict = None) -> str:
    """Genera una recomendación accionable basada en el score y factores."""

    if score <= 2.0:
        return "Condiciones normales. Mantener velocidad y distancia de seguridad."

    if score <= 4.0:
        recs = ["Precaución moderada."]
        if "rain" in factors or "fog" in factors:
            recs.append("Encender luces y reducir velocidad por condiciones climáticas.")
        if "pedestrian_zone" in factors:
            recs.append("Zona con peatones, mantener atención.")
        return " ".join(recs)

    if score <= 7.0:
        recs = ["⚠️ Riesgo ALTO."]
        if "pedestrian_zone" in factors:
            recs.append("Reducir velocidad a 30km/h, peatones en la vía.")
        if "rain" in factors or "fog" in factors:
            recs.append("Visibilidad reducida, aumentar distancia de frenado.")
        if "driver_fatigue" in factors:
            hours = metadata.get("hours_driving", 0) if metadata else 0
            recs.append(f"Llevas {hours:.0f}h conduciendo, buscar punto de descanso.")
        if "road_damage" in factors:
            recs.append("Daño en la vía detectado, esquivar con precaución.")
        if "obstacle_detected" in factors:
            recs.append("Obstáculo detectado, reducir velocidad inmediatamente.")
        return " ".join(recs)

    # score > 7.0
    recs = ["🚨 Riesgo CRÍTICO. Acción inmediata requerida."]
    if "pedestrian_zone" in factors:
        recs.append("Detener vehículo si es seguro, peatones en peligro.")
    if "driver_fatigue" in factors:
        recs.append("PARAR EN EL PRÓXIMO PUNTO SEGURO. Fatiga extrema detectada.")
    if "speeding" in factors:
        recs.append("Reducir velocidad AHORA.")
    if "obstacle_detected" in factors:
        recs.append("Obstáculo peligroso adelante, frenar de forma controlada.")
    return " ".join(recs)


# === Versión con IA (Gemini) ===
def evaluate_risk_with_ai(
    detections: list[Detection],
    metadata: dict = None,
) -> RiskScore:
    """
    Evalúa riesgo usando Gemini para un análisis más sofisticado.
    Fallback a evaluate_risk() si Gemini falla.
    """
    try:
        from google import genai as genai_module
        
        client = genai_module.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        
        # Cargar prompt del oraculo
        prompt_path = Path(__file__).parent / "prompts" / "oraculo_system.md"
        system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "Eres un evaluador de riesgo."

        # Preparar contexto
        det_text = "\n".join(
            f"- {d.label} (severidad: {d.severity}, confianza: {d.confidence:.0%}): {d.description}"
            for d in detections
        )

        meta_text = json.dumps(metadata or {}, ensure_ascii=False, indent=2)

        prompt = f"""Evalúa el riesgo de esta escena de transporte terrestre.

DETECCIONES:
{det_text}

CONTEXTO:
{meta_text}

Responde en JSON con: score (0-10), factors (lista), recommendation (texto accionable)."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=genai_module.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            ),
        )

        result = json.loads(response.text)
        return RiskScore(
            score=float(result.get("score", 5.0)),
            factors=result.get("factors", []),
            recommendation=result.get("recommendation", ""),
            historical_incidents=metadata.get("historical_incidents", 0) if metadata else 0,
        )

    except Exception as e:
        logger.warning(f"Gemini falló para Oráculo, usando reglas: {e}")
        return evaluate_risk(detections, metadata)


# === Mocks ===
def _mock_risk_score() -> RiskScore:
    """Score mock para desarrollo."""
    return RiskScore(
        score=7.3,
        factors=["pedestrian_zone", "rain", "driving_at_night", "driver_fatigue"],
        recommendation=(
            "⚠️ Riesgo ALTO. Reducir velocidad a 30km/h, peatones en la vía. "
            "Visibilidad reducida, aumentar distancia de frenado. "
            "Llevas 4h conduciendo, buscar punto de descanso."
        ),
        historical_incidents=5,
    )


# === Test rápido ===
if __name__ == "__main__":
    from agents.centinela import _mock_detections

    print("🛡️ GUARDIAN — Test del Agente Oráculo")
    print("=" * 50)

    # Escenario 1: Día normal
    print("\n📋 Escenario 1: Día normal, pocas detecciones")
    detections_normal = [
        Detection("vehicle", 0.9, [0.3, 0.4, 0.2, 0.15], "low", "Auto a distancia segura"),
        Detection("sign", 0.95, [0.8, 0.2, 0.1, 0.1], "low", "Señal de velocidad"),
    ]
    result1 = evaluate_risk(detections_normal, {"weather": "sunny", "time_of_day": "morning"})
    print(f"  Score: {result1.score}/10 ({result1.level})")
    print(f"  Factores: {result1.factors}")
    print(f"  Recomendación: {result1.recommendation}")

    # Escenario 2: Peligroso
    print("\n📋 Escenario 2: Noche + lluvia + peatón + fatiga")
    detections_danger = [
        Detection("pedestrian", 0.87, [0.6, 0.5, 0.05, 0.18], "high", "Peatón cruzando"),
        Detection("weather_hazard", 0.8, [0.0, 0.0, 1.0, 0.3], "medium", "Lluvia intensa"),
        Detection("vehicle", 0.92, [0.4, 0.4, 0.15, 0.1], "medium", "Vehículo frenando"),
    ]
    result2 = evaluate_risk(
        detections_danger,
        {"weather": "rain", "time_of_day": "night", "hours_driving": 5.5},
    )
    print(f"  Score: {result2.score}/10 ({result2.level})")
    print(f"  Factores: {result2.factors}")
    print(f"  Recomendación: {result2.recommendation}")

    # Escenario 3: Mock
    print("\n📋 Escenario 3: Mock")
    result3 = evaluate_risk([], mock=True)
    print(f"  Score: {result3.score}/10 ({result3.level})")
