"""
GUARDIAN - Carga de Dataset de Dashcam
=======================================
Script para cargar videos/frames de dashcam en un dataset de FiftyOne.
"""

import os
import glob
from datetime import datetime
from pathlib import Path
import fiftyone as fo

# Ajustamos import para correr como módulo o directo
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import DATASET_NAME, FRAMES_DIR

def load_frames_dataset():
    """
    Carga frames de dashcam en un dataset de FiftyOne con metadata mock.
    """
    print(f"Cargando dataset '{DATASET_NAME}'...")
    
    # Eliminar dataset anterior si existe para tener una demo limpia
    if fo.dataset_exists(DATASET_NAME):
        dataset = fo.load_dataset(DATASET_NAME)
        dataset.clear()
    else:
        dataset = fo.Dataset(DATASET_NAME)
    
    # Asegurar que el directorio exista
    os.makedirs(FRAMES_DIR, exist_ok=True)
    
    filepaths = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.*")))
    
    if not filepaths:
        print(f"⚠️ No hay imágenes en {FRAMES_DIR}. Por favor, añade imágenes primero.")
        return dataset
        
    samples = []
    for filepath in filepaths:
        if not filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        sample = fo.Sample(filepath=filepath)
        # Añadimos la metadata (esto lo debía hacer Rol 1)
        sample["vehicle_id"] = "VH-001"
        sample["driver_id"] = "DR-001"
        sample["timestamp"] = datetime.now().isoformat()
        samples.append(sample)

    dataset.add_samples(samples)
    dataset.persistent = True
    print(f"✅ Dataset '{DATASET_NAME}' cargado exitosamente con {len(dataset)} imágenes.")
    
    return dataset

if __name__ == "__main__":
    load_frames_dataset()
