import os
import time
import cv2
import numpy as np
import mss
from client.config import DEBUG_SAVE_FRAMES, DEBUG_DIR, scale_roi, MONITOR_INDEX

class ScreenCapturer:
    def __init__(self, monitor_index=None):
        """
        monitor_index: Indeks monitora do przechwytywania (None automatycznie wykrywa i wybiera środkowy monitor).
        """
        self.sct = mss.mss()
        
        # Znajdź fizyczne monitory i wybierz środkowy jako domyślny (posortowany po współrzędnej 'left')
        physical_monitors = self.sct.monitors[1:]
        if physical_monitors:
            sorted_monitors = sorted(physical_monitors, key=lambda m: m["left"])
            auto_middle_monitor = sorted_monitors[len(sorted_monitors) // 2]
            auto_middle_index = self.sct.monitors.index(auto_middle_monitor)
        else:
            auto_middle_monitor = self.sct.monitors[0]
            auto_middle_index = 0

        # Pobierz indeks z parametru lub użyj automatycznie wykrytego środkowego monitora
        if monitor_index is None:
            monitor_index = auto_middle_index
            
        print("[ScreenCapturer] Wykryte ekrany w systemie:")
        for i, mon in enumerate(self.sct.monitors):
            desc = "Wirtualny pulpit (wszystkie ekrany)" if i == 0 else f"Fizyczny ekran #{i}"
            is_middle = " [ŚRODKOWY]" if (physical_monitors and mon == auto_middle_monitor) else ""
            print(f"  Monitor #{i} ({desc}): {mon['width']}x{mon['height']} na pozycji (left={mon['left']}, top={mon['top']}){is_middle}")
            
        # Wybieramy odpowiedni monitor (zapobiegamy wyborowi wirtualnego pulpitu #0 przy wielu monitorach)
        if monitor_index == 0:
            print(f"[ScreenCapturer] Wybrano monitor #0 (wirtualny pulpit). Wymuszam środkowy fizyczny ekran #{auto_middle_index}.")
            monitor_index = auto_middle_index

        if len(self.sct.monitors) > monitor_index and monitor_index > 0:
            self.monitor = self.sct.monitors[monitor_index]
        else:
            print(f"[ScreenCapturer] OSTRZEŻENIE: Wybrany monitor #{monitor_index} nie istnieje! Wybieram środkowy ekran #{auto_middle_index}.")
            self.monitor = self.sct.monitors[auto_middle_index]
            monitor_index = auto_middle_index
            
        self.width = self.monitor["width"]
        self.height = self.monitor["height"]
        
        # Informacja o wybranym monitorze
        print(f"[ScreenCapturer] Wybrano do przechwytywania: Monitor #{monitor_index} ({self.width}x{self.height})")
        
        if DEBUG_SAVE_FRAMES:
            if not os.path.exists(DEBUG_DIR):
                os.makedirs(DEBUG_DIR)
                print(f"[ScreenCapturer] Utworzono katalog debugowania: {DEBUG_DIR}")

    def capture_frame(self):
        """
        Pobiera aktualną klatkę z monitora jako tablicę numpy (BGR - kompatybilną z OpenCV).
        """
        try:
            # Szybki zrzut za pomocą mss
            screenshot = self.sct.grab(self.monitor)
            # Konwersja BGRA (mss) do BGR (OpenCV)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception as e:
            print(f"[ScreenCapturer] Błąd przechwytywania ekranu: {e}")
            return None

    def get_roi_slice(self, frame, roi_1920x1080):
        """
        Wycina określony fragment (ROI) z klatki ekranu, automatycznie skalując współrzędne.
        roi_1920x1080: Słownik {"left": ..., "top": ..., "width": ..., "height": ...}
        """
        if frame is None:
            return None
            
        current_res = (self.width, self.height)
        scaled = scale_roi(roi_1920x1080, current_res)
        x_min = scaled["left"]
        y_min = scaled["top"]
        x_max = x_min + scaled["width"]
        y_max = y_min + scaled["height"]
        
        # Ograniczenie współrzędnych do wymiarów klatki, aby uniknąć błędów wycinania
        h, w = frame.shape[:2]
        x_min = max(0, min(x_min, w - 1))
        y_min = max(0, min(y_min, h - 1))
        x_max = max(0, min(x_max, w))
        y_max = max(0, min(y_max, h))
        
        if x_max <= x_min or y_max <= y_min:
            return None
            
        return frame[y_min:y_max, x_min:x_max]

    def save_debug_image(self, frame):
        """
        Zapisuje pełną klatkę do katalogu debugowania. Ułatwia to kalibrację ROI w programach graficznych.
        """
        if frame is None:
            return
        
        filename = f"tft_capture_{int(time.time())}.png"
        filepath = os.path.join(DEBUG_DIR, filename)
        
        # Rysowanie pomocniczych linii dla zdefiniowanego ROI na kopii obrazu w celach diagnostycznych
        debug_frame = frame.copy()
        
        # Zapis czystego zrzutu ekranu
        cv2.imwrite(filepath, frame)
        print(f"[ScreenCapturer] Zapisano klatkę testową do kalibracji: {filepath}")
        return filepath
