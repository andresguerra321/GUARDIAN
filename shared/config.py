import os

# Configuración de la API de Gemini (requerida en la Hora 0)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Constantes del Proyecto
PROJECT_NAME = "GUARDIAN"
VERSION = "1.0"
MAX_RISK_SCORE = 10.0
SEVERITY_LEVELS = ["info", "warning", "danger", "emergency"]