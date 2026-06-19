import fiftyone as fo

def main():
    print("🔥 Levantando la demo maestra de GUARDIAN...")
    
    datasets = fo.list_datasets()
    if "guardian" not in datasets:
        print("⚠️ Grave: no existe el dataset 'guardian'.")
        print("Dile al Rol 1 que ejecute 'load_dashcam.py' primero para cargar los datos.")
        return

    dataset = fo.load_dataset("guardian")
    print(f"📊 Dataset 'guardian' cargado con {len(dataset)} frames.")

    print("🖥️ Abriendo FiftyOne App para la magia...")
    session = fo.launch_app(dataset)
    session.wait()

if __name__ == "__main__":
    main()