"""
GUARDIAN - Extractor de Frames
================================

Extrae frames de archivos de video para cargarlos en FiftyOne.
Soporta videos locales o descarga directa desde YouTube con yt-dlp.

Uso:
  python scripts/extract_frames.py --input demo-assets/videos/bucaramanga.mp4 --output demo-assets/frames/ --fps 1
  python scripts/extract_frames.py --input "https://youtu.be/Nc_mfYNlFWU" --output demo-assets/frames/ --fps 1
"""

import argparse
import os
import subprocess
import sys
from shutil import which


def check_tool(name):
    if which(name) is None:
        print(f"[ERROR] '{name}' no esta instalado.")
        sys.exit(1)


def run(cmd):
    print(f"\n$ {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[ERROR] el comando fallo (codigo {result.returncode})")
        sys.exit(1)


def maybe_download(input_path):
    """Si input_path es una URL de YouTube, lo descarga primero. Si es un
    archivo local, lo devuelve tal cual."""
    if input_path.startswith("http://") or input_path.startswith("https://"):
        check_tool("yt-dlp")
        os.makedirs("demo-assets/videos", exist_ok=True)
        out_path = "demo-assets/videos/bucaramanga.mp4"
        run(["yt-dlp", "-f", "mp4", "-o", out_path, "--force-overwrites", input_path])
        return out_path
    return input_path


def extract_frames(video_path: str, output_dir: str, fps: int = 2, max_frames: int = 100):
    """
    Extrae frames de un video a intervalos regulares.

    Args:
        video_path: Ruta al video (o URL de YouTube)
        output_dir: Directorio donde guardar los frames
        fps: Frames por segundo a extraer
        max_frames: Maximo de frames a extraer
    """
    video_path = maybe_download(video_path)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No existe el video: {video_path}")

    check_tool("ffmpeg")
    os.makedirs(output_dir, exist_ok=True)

    # Limpia frames viejos para no mezclar tomas anteriores
    for f in os.listdir(output_dir):
        if f.endswith(".jpg"):
            os.remove(os.path.join(output_dir, f))

    pattern = os.path.join(output_dir, "frame_%04d.jpg")
    run(["ffmpeg", "-i", video_path, "-vf", f"fps={fps}", "-q:v", "2",
         "-frames:v", str(max_frames), pattern])

    n = len([f for f in os.listdir(output_dir) if f.endswith(".jpg")])
    print(f"\n[ok] {n} frames extraidos en {output_dir}/")
    return n


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extraer frames de video")
    parser.add_argument("--input", required=True, help="Ruta al video o URL de YouTube")
    parser.add_argument("--output", default="demo-assets/frames/", help="Directorio de salida")
    parser.add_argument("--fps", type=int, default=2, help="Frames por segundo")
    parser.add_argument("--max-frames", type=int, default=100, help="Máximo de frames")
    args = parser.parse_args()

    extract_frames(args.input, args.output, args.fps, args.max_frames)
