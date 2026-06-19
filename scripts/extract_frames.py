"""
GUARDIAN - Extractor de Frames
================================

Extrae frames de archivos de video para cargarlos en FiftyOne.

Uso:
  python scripts/extract_frames.py --input demo-assets/videos/ --output demo-assets/frames/ --fps 2

TODO (Rol 1):
  - [ ] Implementar extracción con OpenCV
  - [ ] Parámetros: input, output, fps, max_frames
"""

import argparse
# import cv2
# import os


def extract_frames(video_path: str, output_dir: str, fps: int = 2, max_frames: int = 100):
    """
    Extrae frames de un video a intervalos regulares.

    Args:
        video_path: Ruta al video
        output_dir: Directorio donde guardar los frames
        fps: Frames por segundo a extraer
        max_frames: Máximo de frames a extraer
    """
    # TODO: Implementar con cv2 - Rol 1
    raise NotImplementedError("Implementar extracción de frames - Rol 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extraer frames de video")
    parser.add_argument("--input", required=True, help="Ruta al video o directorio de videos")
    parser.add_argument("--output", default="demo-assets/frames/", help="Directorio de salida")
    parser.add_argument("--fps", type=int, default=2, help="Frames por segundo")
    parser.add_argument("--max-frames", type=int, default=100, help="Máximo de frames")
    args = parser.parse_args()

    extract_frames(args.input, args.output, args.fps, args.max_frames)
