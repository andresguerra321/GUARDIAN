"""
GUARDIAN · Rol 1 — Carga de dashcam en FiftyOne
================================================
Objetivo de la HORA 1: tener un fo.Dataset navegable en la App con >=10 frames.

Estrategia de 3 niveles (usa el primero que funcione, NO te bloquees):
  NIVEL A  -> Video propio de Bucaramanga (mejor impacto para el jurado local)
  NIVEL B  -> Video descargado de YouTube con yt-dlp
  NIVEL C  -> Zoo de FiftyOne (quickstart-video) como fallback inmediato

Uso:
  python load_dashcam.py                     # usa fallback del zoo (cero fricción)
  python load_dashcam.py --video ruta.mp4    # usa tu video (Bucaramanga)
  python load_dashcam.py --frames-dir carpeta_frames/   # usa frames JPEG sueltos
"""

import argparse
import os
from pathlib import Path
import fiftyone as fo
import fiftyone.zoo as foz

DATASET_NAME = "guardian"   # nombre acordado con el equipo. NO lo cambies sin avisar.

# Ajustamos import para correr como módulo o directo
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import DATASET_NAME, FRAMES_DIR

def reset_dataset(name=DATASET_NAME):
    """Borra el dataset si ya existe, para poder recargar limpio."""
    if fo.dataset_exists(name):
        fo.delete_dataset(name)
        print(f"[reset] dataset '{name}' anterior eliminado")


def from_video(video_path):
    """NIVEL A/B: cargar un único video como sample de video + extraer frames."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No existe el video: {video_path}")

    reset_dataset()
    dataset = fo.Dataset(DATASET_NAME, persistent=True)

    # Metadata real del video (resolución, fps, duración) calculada por FiftyOne
    metadata = fo.VideoMetadata.build_for(video_path)
    sample = fo.Sample(filepath=video_path, metadata=metadata)
    dataset.add_sample(sample)

    # Pre-poblar la estructura de frames para poder navegarlos en la App
    dataset.ensure_frames()
    dataset.compute_metadata()

    print(f"[ok] video cargado: {video_path}")
    print(f"[ok] frames disponibles: {metadata.total_frame_count}")
    return dataset


def from_frames_dir(frames_dir):
    """NIVEL B/C alterno: cargar una carpeta de frames JPEG como dataset de imagenes.

    Esto es lo MAS robusto para un hackathon: cero problemas de codec de video.
    Cada frame es un sample independiente -> los operators del Rol 2 corren directo.
    """
    if not os.path.isdir(frames_dir):
        raise NotADirectoryError(f"No existe la carpeta: {frames_dir}")

    reset_dataset()
    dataset = fo.Dataset.from_dir(
        dataset_dir=frames_dir,
        dataset_type=fo.types.ImageDirectory,
        name=DATASET_NAME,
    )
    dataset.persistent = True
    dataset.compute_metadata()
    print(f"[ok] {len(dataset)} frames cargados desde {frames_dir}")
    return dataset


def from_zoo():
    """NIVEL C (fallback): video de dashcam del zoo, ya viene con detecciones.

    Permite que TODO el equipo arranque en la hora 0 sin esperar tu video.
    """
    reset_dataset()
    src = foz.load_zoo_dataset("quickstart-video")

    # Lo clonamos al nombre del equipo y lo dejamos persistente
    dataset = src.clone(DATASET_NAME, persistent=True)
    dataset.ensure_frames()
    dataset.compute_metadata()
    print(f"[ok] fallback del zoo cargado como '{DATASET_NAME}'")
    print(f"[ok] {len(dataset)} videos, frames navegables")
    return dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="ruta a un video .mp4 de dashcam")
    parser.add_argument("--frames-dir", help="carpeta con frames .jpg")
    args = parser.parse_args()

    if args.video:
        dataset = from_video(args.video)
    elif args.frames_dir:
        dataset = from_frames_dir(args.frames_dir)
    else:
        print("[info] sin --video ni --frames-dir: usando fallback del zoo")
        dataset = from_zoo()

    print("\n=== RESUMEN ===")
    print(f"Dataset: {dataset.name}")
    print(f"Media type: {dataset.media_type}")
    print(f"Samples: {len(dataset)}")
    print(f"Persistente: {dataset.persistent}")
    print("\nPara verlo:  fiftyone app launch")
    print(f"En Python :  fo.load_dataset('{DATASET_NAME}')")
    
    return dataset

if __name__ == "__main__":
    main()