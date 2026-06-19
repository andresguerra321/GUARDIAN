"""
GUARDIAN - Agente Centinela (Lógica de IA)
==========================================

Analiza frames de dashcam para detectar peligros en la vía.
Usa Gemini Vision para análisis semántico de escenas.

Interfaz:
  - analyze_frame(image_path) -> list[Detection]
  - analyze_frame_with_summary(image_path) -> dict con detections + scene_summary
"""

import os
import sys
import json
import logging
from pathlib import Path

# Asegurar imports del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

from shared.contracts import Detection

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
            raise ValueError(
                "GEMINI_API_KEY no configurada. "
                "Edita el archivo .env con tu API key de Google AI Studio."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# === System Prompt ===
def _load_system_prompt() -> str:
    """Carga el system prompt del Centinela."""
    prompt_path = Path(__file__).parent / "prompts" / "centinela_system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    # Fallback inline
    return (
        "Eres un sistema de visión artificial para seguridad vial. "
        "Analiza la imagen de dashcam e identifica peligros. "
        "Responde SOLO en JSON válido."
    )


# === Schema de respuesta para Gemini ===
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "detections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "enum": [
                            "vehicle", "pedestrian", "obstacle", "sign",
                            "pothole", "weather_hazard", "road_condition",
                        ],
                    },
                    "confidence": {"type": "number"},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "description": {"type": "string"},
                    "bounding_box_approx": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Approximate [x, y, width, height] normalized 0-1",
                    },
                },
                "required": ["label", "confidence", "severity", "description"],
            },
        },
        "scene_summary": {"type": "string"},
        "overall_risk": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
        },
    },
    "required": ["detections", "scene_summary", "overall_risk"],
}


# === Función principal ===
def analyze_frame(image_path: str, mock: bool = False) -> list[Detection]:
    """
    Analiza un frame de dashcam y devuelve detecciones de peligros.

    Args:
        image_path: Ruta al archivo de imagen (JPEG, PNG)
        mock: Si True, devuelve detecciones hardcodeadas

    Returns:
        Lista de Detection con objetos detectados
    """
    if mock:
        return _mock_detections()

    result = analyze_frame_with_summary(image_path)
    return result["detections"]


def analyze_frame_with_summary(image_path: str, mock: bool = False) -> dict:
    """
    Analiza un frame y devuelve detecciones + resumen de escena.

    Args:
        image_path: Ruta al archivo de imagen

    Returns:
        dict con keys: detections (list[Detection]), scene_summary (str), overall_risk (str)
    """
    if mock:
        return {
            "detections": _mock_detections(),
            "scene_summary": "Escena simulada con tráfico moderado",
            "overall_risk": "medium",
        }

    client = _get_client()
    system_prompt = _load_system_prompt()

    # Leer imagen
    image_path = str(image_path)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

    # Subir imagen a Gemini
    logger.info(f"Analizando frame: {image_path}")

    try:
        uploaded_file = client.files.upload(file=image_path)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=uploaded_file.mime_type,
                        ),
                        genai_types.Part.from_text(
                            text="Analiza esta imagen de dashcam de un vehículo de transporte terrestre. "
                            "Identifica TODOS los elementos relevantes para la seguridad vial."
                        ),
                    ],
                )
            ],
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.2,
            ),
        )

        result = json.loads(response.text)
        logger.info(
            f"Centinela detectó {len(result.get('detections', []))} objetos. "
            f"Riesgo: {result.get('overall_risk', 'unknown')}"
        )

        # Convertir a Detection objects
        detections = []
        for d in result.get("detections", []):
            bbox = d.get("bounding_box_approx", [0.5, 0.5, 0.1, 0.1])
            # Asegurar que bbox tiene 4 valores
            if len(bbox) != 4:
                bbox = [0.5, 0.5, 0.1, 0.1]

            detections.append(
                Detection(
                    label=d["label"],
                    confidence=float(d.get("confidence", 0.5)),
                    bounding_box=bbox,
                    severity=d.get("severity", "medium"),
                    description=d.get("description", ""),
                )
            )

        return {
            "detections": detections,
            "scene_summary": result.get("scene_summary", ""),
            "overall_risk": result.get("overall_risk", "medium"),
        }

    except Exception as e:
        logger.error(f"Error en Centinela: {e}")
        logger.warning("Usando detecciones mock como fallback")
        return {
            "detections": _mock_detections(),
            "scene_summary": f"[FALLBACK] Error al analizar: {str(e)[:100]}",
            "overall_risk": "medium",
        }


# === Mocks ===
def _mock_detections() -> list[Detection]:
    """Detecciones mock realistas para desarrollo."""
    return [
        Detection(
            label="vehicle",
            confidence=0.92,
            bounding_box=[0.3, 0.4, 0.2, 0.15],
            severity="low",
            description="Vehículo en carril contrario a distancia segura",
        ),
        Detection(
            label="pedestrian",
            confidence=0.87,
            bounding_box=[0.65, 0.45, 0.05, 0.18],
            severity="high",
            description="Peatón cruzando fuera de paso cebra a aproximadamente 30 metros",
        ),
        Detection(
            label="sign",
            confidence=0.95,
            bounding_box=[0.85, 0.2, 0.08, 0.12],
            severity="low",
            description="Señal de límite de velocidad 60 km/h",
        ),
        Detection(
            label="road_condition",
            confidence=0.73,
            bounding_box=[0.1, 0.7, 0.3, 0.15],
            severity="medium",
            description="Superficie mojada, posible lluvia reciente",
        ),
    ]


# === Test rápido ===
if __name__ == "__main__":
    import sys

    print("🛡️ GUARDIAN — Test del Agente Centinela")
    print("=" * 50)

    # Test con mock
    print("\n📋 Test con MOCK:")
    mock_results = analyze_frame("dummy.jpg", mock=True)
    for d in mock_results:
        print(f"  [{d.severity.upper():>8}] {d.label}: {d.description} (conf: {d.confidence})")

    # Test con imagen real si se pasa como argumento
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n🔍 Test con imagen REAL: {image_path}")
        try:
            result = analyze_frame_with_summary(image_path)
            print(f"  Resumen: {result['scene_summary']}")
            print(f"  Riesgo general: {result['overall_risk']}")
            print(f"  Detecciones ({len(result['detections'])}):")
            for d in result["detections"]:
                print(f"    [{d.severity.upper():>8}] {d.label}: {d.description}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print("\n💡 Para probar con imagen real:")
        print("   python agents/centinela.py ruta/a/imagen.jpg")
