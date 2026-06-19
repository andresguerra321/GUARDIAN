# 🛡️ GUARDIAN

**G**estión **U**nificada de **A**lertas, **R**iesgo, **D**etección e **I**nteligencia para **A**gentes de tra**N**sporte

> Sistema de seguridad predictiva para transporte terrestre basado en múltiples agentes de IA colaborativos, construido sobre la plataforma [FiftyOne](https://docs.voxel51.com/) de Voxel51.

---

## 🎯 ¿Qué es GUARDIAN?

GUARDIAN es un sistema que utiliza Computer Vision e Inteligencia Artificial para **predecir y prevenir accidentes** en transporte terrestre. A diferencia de los sistemas reactivos tradicionales, GUARDIAN opera con tres agentes de IA que colaboran entre sí:

| Agente | Función |
|--------|---------|
| 🎙️ **Copiloto** | Asistente conversacional que interactúa con el conductor |
| 👁️ **Centinela** | Analiza video de dashcam para detectar peligros |
| 🗺️ **Oráculo** | Evalúa riesgo por zona combinando detecciones, clima e historial |

## 🏗️ Arquitectura

FiftyOne es la **plataforma central** del proyecto:

- **Datasets**: Almacenan frames de dashcam con metadatos (GPS, velocidad, conductor)
- **Operators**: Ejecutan los pipelines de detección y evaluación de riesgo
- **Panels**: Proporcionan la interfaz visual del centro de control

## 📁 Estructura del Proyecto

```
guardian/
├── plugins/                    ← Plugins de FiftyOne (core del proyecto)
│   ├── guardian-centinela/      ← Operator de detección de peligros
│   ├── guardian-oraculo/        ← Operator de evaluación de riesgo
│   ├── guardian-copiloto/       ← Operator del asistente conversacional
│   └── guardian-dashboard/      ← Panel del centro de control
├── agents/                     ← Lógica de IA de los agentes
│   └── prompts/                ← System prompts de cada agente
├── datasets/                   ← Scripts de carga y preparación de datos
├── shared/                     ← Código compartido (contratos, config)
├── demo-assets/                ← Assets para la demo (videos, frames, escenarios)
├── scripts/                    ← Scripts de utilidad y automatización
└── docs/                       ← Documentación del equipo
```

## 🚀 Setup Rápido

### Prerrequisitos

- Python 3.9+
- pip
- Git
- API key de Gemini (Google AI)

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/andresguerra321/GUARDIAN.git
cd GUARDIAN

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API key
cp .env.example .env
# Editar .env con tu API key de Gemini

# 5. Registrar plugins de FiftyOne
fiftyone plugins create guardian-centinela --from plugins/guardian-centinela
fiftyone plugins create guardian-oraculo --from plugins/guardian-oraculo
fiftyone plugins create guardian-copiloto --from plugins/guardian-copiloto
fiftyone plugins create guardian-dashboard --from plugins/guardian-dashboard

# 6. Lanzar FiftyOne
fiftyone app launch
```

## 👥 Equipo

| Rol | Responsabilidad |
|-----|----------------|
| 🟢 R1 | Ingeniero de Datos y Dataset |
| 🔵 R2 | Ingeniero de Plugins (Operators) |
| 🟣 R3 | Ingeniero de Panel (Dashboard) |
| 🟠 R4 | Ingeniero de IA / Agentes |
| 🔴 R5 | Integración, Contratos y Presentación |

## 📄 Licencia

MIT

---

*Desarrollado para la Hackathon Voxel51/FiftyOne 2026*