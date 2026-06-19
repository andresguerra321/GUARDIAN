"""
GUARDIAN - Carga de Dataset de Dashcam
=======================================

Script para cargar videos/frames de dashcam en un dataset de FiftyOne.

Uso:
  python datasets/load_dashcam.py

TODO (Rol 1):
  - [ ] Implementar carga de frames desde demo-assets/frames/
  - [ ] Implementar carga de videos desde demo-assets/videos/
  - [ ] Añadir metadata básica (timestamp, vehicle_id, driver_id)
  - [ ] Verificar que el dataset se ve en FiftyOne App
"""

# import fiftyone as fo
# from shared.config import DATASET_NAME, FRAMES_DIR, VIDEOS_DIR


def load_frames_dataset():
    """
    Carga frames de dashcam en un dataset de FiftyOne.

    Crea un dataset con samples de imagen, cada uno con metadata:
      - vehicle_id
      - driver_id
      - timestamp
      - gps (mock)
    """
    # TODO: Implementar - Rol 1
    #
    # dataset = fo.Dataset(DATASET_NAME, overwrite=True)
    #
    # for frame_path in sorted(glob(os.path.join(FRAMES_DIR, "*.jpg"))):
    #     sample = fo.Sample(filepath=frame_path)
    #     sample["vehicle_id"] = "VH-001"
    #     sample["driver_id"] = "DR-001"
    #     sample["timestamp"] = datetime.now().isoformat()
    #     dataset.add_sample(sample)
    #
    # dataset.persistent = True
    # print(f"Dataset '{DATASET_NAME}' creado con {len(dataset)} samples")

    raise NotImplementedError("Implementar carga de dataset - Rol 1")


if __name__ == "__main__":
    load_frames_dataset()
