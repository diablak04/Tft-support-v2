# client/debug_roi.py
import os
import cv2
import time
from client.capture import ScreenCapturer
from client.config import ROI_CONFIG, SHOP_SLOTS_ROI, DEBUG_DIR

def debug_alignment():
    print("=== TFT ROI CALIBRATION UTILITY ===")
    capturer = ScreenCapturer(monitor_index=None)
    
    # Przechwyć klatkę
    print("Pobieranie zrzutu ekranu...")
    frame = capturer.capture_frame()
    if frame is None:
        print("BŁĄD: Nie udało się pobrać obrazu z ekranu!")
        return

    h, w = frame.shape[:2]
    print(f"Rozdzielczość przechwyconego obrazu: {w}x{h}")
    
    os.makedirs(DEBUG_DIR, exist_ok=True)
    
    # 1. Rysuj prostokąty ROI na kopii pełnej klatki
    annotated_frame = frame.copy()
    
    # Rysuj statyczne ROI z ROI_CONFIG
    colors = {
        "gold": (0, 255, 255),       # Żółty
        "level": (255, 0, 0),        # Niebieski
        "xp": (255, 0, 255),         # Różowy
        "stage": (0, 255, 0),        # Zielony
        "player_hp": (0, 0, 255),    # Czerwony
        "odswiez": (128, 128, 128),
        "procenty": (255, 128, 0),
        "mapa": (0, 128, 255)
    }
    
    for name, roi in ROI_CONFIG.items():
        # Wycięcie i zapisanie pojedynczego kafelka debugowego
        crop = capturer.get_roi_slice(frame, roi)
        if crop is not None and crop.size > 0:
            crop_path = os.path.join(DEBUG_DIR, f"crop_{name}.png")
            cv2.imwrite(crop_path, crop)
            print(f" -> Zapisano wycinek dla '{name}': {crop_path}")
            
        # Narysowanie prostokąta na pełnym obrazie
        from client.config import scale_roi
        scaled_roi = scale_roi(roi, (w, h))
        x_min = scaled_roi["left"]
        y_min = scaled_roi["top"]
        x_max = x_min + scaled_roi["width"]
        y_max = y_min + scaled_roi["height"]
        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), colors.get(name, (255, 255, 255)), 2)
        cv2.putText(annotated_frame, name, (x_min, max(15, y_min - 5)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors.get(name, (255, 255, 255)), 1)

    # Rysuj sloty sklepu
    for i, roi in enumerate(SHOP_SLOTS_ROI):
        crop = capturer.get_roi_slice(frame, roi)
        if crop is not None and crop.size > 0:
            crop_path = os.path.join(DEBUG_DIR, f"crop_shop_slot_{i+1}.png")
            cv2.imwrite(crop_path, crop)
            
        from client.config import scale_roi
        scaled_roi = scale_roi(roi, (w, h))
        x_min = scaled_roi["left"]
        y_min = scaled_roi["top"]
        x_max = x_min + scaled_roi["width"]
        y_max = y_min + scaled_roi["height"]
        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)
        cv2.putText(annotated_frame, f"shop_{i+1}", (x_min, y_min - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # Zapisz pełny obraz z zaznaczonymi obszarami
    full_path = os.path.join(DEBUG_DIR, "roi_calibration.png")
    cv2.imwrite(full_path, annotated_frame)
    
    print("\n=== PODSUMOWANIE ===")
    print(f"Zapisano pełny obraz kalibracji: {full_path}")
    print("Otwórz ten plik i zobacz, czy prostokąty pokrywają się ze wskaźnikami w grze.")
    print(f"W folderze {DEBUG_DIR} znajdziesz też pojedyncze wycinki (crop_*.png). Sprawdź je!")

if __name__ == "__main__":
    debug_alignment()
