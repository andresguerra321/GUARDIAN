"""
GUARDIAN - Script Maestro de Demo
==================================

Ejecuta toda la pipeline de GUARDIAN de inicio a fin para la demo.
"""

import os
import sys
from pathlib import Path
import fiftyone as fo

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import FRAMES_DIR
from datasets.load_dashcam import from_frames_dir

def run_demo():
    """Ejecuta la demo completa de GUARDIAN."""
    print("🛡️ GUARDIAN — Iniciando Demo")
    print("=" * 50)
    
    # 1. Configurar ruta de plugins para FiftyOne automáticamente
    plugins_dir = str(Path(__file__).parent.parent / "plugins")
    os.environ["FIFTYONE_PLUGINS_DIR"] = plugins_dir
    print(f"🔌 Directorio de plugins configurado en: {plugins_dir}")

    # 2. Cargar dataset usando frames_dir
    dataset = from_frames_dir(FRAMES_DIR)

    # 3. Lanzar FiftyOne App
    print("\n🚀 Lanzando Centro de Control FiftyOne...")
    session = fo.launch_app(dataset)
    
    print("\n" + "="*50)
    print("✅ GUARDIAN está en línea.")
    print("➡️ Entra a http://localhost:5151 en tu navegador.")
    print("➡️ Presiona '`' (acento grave) o usa la barra superior para ejecutar los Agentes.")
    print("="*50 + "\n")
    
    # Mantener el proceso vivo
    session.wait(-1)

if __name__ == "__main__":
    run_demo()
