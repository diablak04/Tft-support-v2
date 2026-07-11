import cv2
import os
import sys

def slice_video(video_path, output_folder, interval_seconds=5):
    """
    Tnie plik wideo (.mp4, .mkv, .avi) na pojedyncze klatki jpg co określoną liczbę sekund.
    Ułatwia przygotowanie zbioru danych (datasetu) do oznaczania w AnyLabeling.
    """
    if not os.path.exists(video_path):
        print(f"BŁĄD: Plik wideo '{video_path}' nie istnieje!")
        print("Upewnij się, że podajesz poprawną ścieżkę do pliku.")
        return False
        
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Utworzono katalog wyjściowy: {output_folder}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"BŁĄD: Nie można otworzyć wideo {video_path}")
        return False
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    # Obliczamy co ile klatek wideo zapisać jedno zdjęcie
    frame_interval = int(fps * interval_seconds)
    if frame_interval <= 0:
        frame_interval = 1
        
    print("=" * 60)
    print(f" WIDEO: {os.path.basename(video_path)}")
    print(f" DŁUGOŚĆ: {duration:.1f}s | FPS: {fps:.2f} | KLATEK ŁĄCZNIE: {total_frames}")
    print(f" USTAWIENIE: Zapis klatki co {interval_seconds}s (co {frame_interval} klatek)")
    print("=" * 60)
    print("Przetwarzanie... (Naciśnij Ctrl+C, aby przerwać)")
    
    frame_count = 0
    saved_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                filename = f"frame_{saved_count:04d}.jpg"
                filepath = os.path.join(output_folder, filename)
                cv2.imwrite(filepath, frame)
                saved_count += 1
                
                # Prosty wskaźnik postępu w konsoli
                sys.stdout.write(f"\rZapisano: {saved_count} klatek... (Czas wideo: {frame_count / fps:.1f}s)")
                sys.stdout.flush()
                
            frame_count += 1
            
    except KeyboardInterrupt:
        print("\n\n[Przerwano] Przetwarzanie zatrzymane przez użytkownika.")
        
    cap.release()
    print(f"\n\nSukces! Wycięto {saved_count} klatek.")
    print(f"Wszystkie zdjęcia znajdują się w folderze: {output_folder}")
    print("Możesz teraz otworzyć AnyLabeling i zaimportować ten katalog!")
    return True

if __name__ == "__main__":
    video_path = r"C:\Users\diabl\Documents\yolo\vid\Dark Star Nami Might Actually Be GIGA BROKEN!!!  TFT Set 17 - CammyTFT (1080p, h264, youtube).mp4"
    output_folder = r"C:\Users\diabl\Documents\yolo\vid\pocietevid"
    
    slice_video(video_path, output_folder, interval_seconds=5)
