"""
GUARDIAN - Configuración Central
=================================

Configuración compartida del proyecto.
Carga variables de entorno y define constantes.

REGLAS:
  - Solo Rol 5 modifica este archivo
  - Todos los demás roles importan de aquí
"""

import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()


# === API Keys ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# === Modelos ===
GEMINI_MODEL = "gemini-2.5-flash"  # Modelo rápido para demo

# === FiftyOne ===
DATASET_NAME = "guardian"
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")

# === Paths ===
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DEMO_ASSETS_DIR = os.path.join(PROJECT_ROOT, "demo-assets")
VIDEOS_DIR = os.path.join(DEMO_ASSETS_DIR, "videos")
FRAMES_DIR = os.path.join(DEMO_ASSETS_DIR, "frames")
SCENARIOS_DIR = os.path.join(DEMO_ASSETS_DIR, "scenarios")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "agents", "prompts")

# === Mock Mode ===
MOCK_MODE = os.getenv("GUARDIAN_MOCK_MODE", "false").lower() == "true"

# === Logging ===
LOG_LEVEL = os.getenv("GUARDIAN_LOG_LEVEL", "INFO")

# === Constantes de Detección ===
DETECTION_LABELS = [
    "vehicle",
    "pedestrian",
    "obstacle",
    "sign",
    "pothole",
    "weather_hazard",
    "road_condition",
]

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
ALERT_TYPES = ["hazard", "fatigue", "compliance", "weather"]
ALERT_SEVERITIES = ["info", "warning", "danger", "emergency"]
