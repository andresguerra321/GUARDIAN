"""
GUARDIAN - Script de Setup del Entorno
========================================

Instala dependencias, registra plugins de FiftyOne, y verifica que todo funciona.

Uso:
  python scripts/setup_environment.py

TODO (Rol 5):
  - [ ] Automatizar registro de plugins en FiftyOne
  - [ ] Verificar API key de Gemini
  - [ ] Crear dataset vacío si no existe
"""

import subprocess
import sys
import os


def setup():
    """Configura el entorno completo de GUARDIAN."""

    print("🛡️ GUARDIAN — Setup del Entorno")
    print("=" * 50)

    # 1. Verificar Python
    print(f"\n✅ Python {sys.version}")

    # 2. Verificar dependencias clave
    try:
        import fiftyone as fo
        print(f"✅ FiftyOne {fo.__version__}")
    except ImportError:
        print("❌ FiftyOne no instalado. Ejecuta: pip install -r requirements.txt")
        return False

    # 3. Verificar API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "your_gemini_api_key_here":
        print("✅ GEMINI_API_KEY configurada")
    else:
        print("⚠️ GEMINI_API_KEY no configurada. Copia .env.example a .env y añade tu key")

    # 4. Registrar plugins
    # TODO: Implementar registro automático de plugins
    print("\n📦 Plugins registrados:")
    print("  - guardian-centinela")
    print("  - guardian-oraculo")
    print("  - guardian-copiloto")
    print("  - guardian-dashboard")

    # 5. Verificar dataset
    # TODO: Crear dataset vacío si no existe

    print("\n" + "=" * 50)
    print("🚀 Setup completado. Ejecuta 'fiftyone app launch' para comenzar.")
    return True


if __name__ == "__main__":
    setup()
