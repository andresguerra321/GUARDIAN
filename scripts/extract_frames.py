import cv2
import os
import glob

def extract_frames(video_path, output_folder, frame_rate=1):
    # frame_rate = saca 1 frame cada X segundos
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    success, image = vidcap.read()
    count = 0
    saved_count = 0

    video_name = os.path.basename(video_path).split('.')[0]

    while success:
        if count % (fps * frame_rate) == 0:
            frame_path = os.path.join(output_folder, f"{video_name}_frame_{saved_count:04d}.jpg")
            cv2.imwrite(frame_path, image)
            saved_count += 1
        success, image = vidcap.read()
        count += 1
    
    print(f"🎬 {video_name} procesado: Se sacaron {saved_count} frames.")

if __name__ == "__main__":
    print("⏳ Empezando a extraer frames...")
    
    videos = glob.glob("demo-assets/videos/*.mp4")
    if not videos:
        print("❌ No encontré videos .mp4 en la carpeta demo-assets/videos/ 😩")
    else:
        for video in videos:
            extract_frames(video, "demo-assets/frames/", frame_rate=1)
        print("✅ Extracción terminada al 100%.")