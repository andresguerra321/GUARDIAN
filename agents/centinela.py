"""
GUARDIAN - Agente Centinela (Lógica de IA)
==========================================

Este módulo contiene la lógica de detección de peligros.
Recibe una imagen (frame de dashcam) y devuelve detecciones.

Interfaz principal:
  - analyze_frame(image_path: str) -> list[Detection]
  - analyze_frame_batch(image_paths: list[str]) -> list[list[Detection]]

Modelos sugeridos:
  - YOLO (ultralytics) para detección de objetos
  - Gemini Vision para análisis semántico de escenas
  - Combinación de ambos para mayor riqueza

TODO (Rol 4):
  - [ ] Implementar analyze_frame() con modelo de detección
  - [ ] Implementar modo mock para desarrollo
  - [ ] Definir clases de detección relevantes para transporte
  - [ ] Manejar errores y timeouts de API
  - [ ] Optimizar para latencia de demo
"""

from shared.contracts import Detection


def analyze_frame(image_path: str, mock: bool = False) -> list[Detection]:
    """
    Analiza un frame de dashcam y devuelve detecciones de peligros.

    Args:
        image_path: Ruta al archivo de imagen
        mock: Si True, devuelve detecciones hardcodeadas para desarrollo

    Returns:
        Lista de Detection con objetos detectados
    """
    if mock:
        return _mock_detections()

    # TODO: Implementar detección real
    # Opción 1: YOLO
    # from ultralytics import YOLO
    # model = YOLO("yolov8n.pt")
    # results = model(image_path)
    #
    # Opción 2: Gemini Vision
    # from google import genai
    # client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # response = client.models.generate_content(...)

    raise NotImplementedError("Implementar detección real - Rol 4")


def _mock_detections() -> list[Detection]:
    """Devuelve detecciones mock para desarrollo sin depender de APIs."""
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
            bounding_box=[0.6, 0.5, 0.05, 0.15],
            severity="high",
            description="Peatón cruzando fuera de paso cebra a 30m",
        ),
    ]
