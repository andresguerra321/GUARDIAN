import os
import subprocess
import sys

def main():
    print("🚀 Iniciando el setup de GUARDIAN...")
    
    # Instalar dependencias
    print("📦 Instalando dependencias del requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print("❌ Uy, paila. Hubo un error instalando las dependencias:", e)
        return
    
    # Chequear si pusieron la API KEY
    if not os.getenv("GEMINI_API_KEY"):
        print("\n⚠️ OJO: Falta configurar la GEMINI_API_KEY.")
        print("Recuerda meterla en tu archivo .env antes de correr los agentes.")
    
    print("\n✅ ¡Entorno coronado! Listos para romperla en el hackathon.")

if __name__ == "__main__":
    main()