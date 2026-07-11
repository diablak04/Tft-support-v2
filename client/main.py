import time
import json
import os
import requests
import cv2
from client.config import (
    CAPTURE_INTERVAL,
    BACKEND_URL,
    ROI_CONFIG,
    SHOP_SLOTS_ROI,
    DEBUG_SAVE_FRAMES,
    SHOW_DETECTION_WINDOW
)
from client.capture import ScreenCapturer
from client.ocr_processor import OCRProcessor
from client.yolo_detector import TFTYoloDetector

def print_cli_dashboard(game_state, mock_yolo, ocr_engine):
    """
    Rysuje elegancki interfejs konsolowy (dashboard) prezentujący aktualny stan rozgrywki.
    """
    # Czyszczenie konsoli w zależności od systemu operacyjnego
    os.system('cls' if os.name == 'nt' else 'clear')
    
    info = game_state["game_info"]
    shop = game_state["shop"]
    board = game_state["board"]
    bench = game_state["bench"]
    items = game_state["items"]
    
    print("=" * 72)
    print("      TFT COMPUTER VISION CLIENT - PASYWNY ANALIZATOR (KOMPUTER #3)      ")
    print("=" * 72)
    yolo_status = "AKTYWNY (MOCK)" if mock_yolo else "AKTYWNY (YOLOv8)"
    print(f" Status: URUCHOMIONY | Silnik OCR: {ocr_engine.upper()} | Model YOLO: {yolo_status}")
    print(f" Interwał: {CAPTURE_INTERVAL}s | Czas zapisu: {time.strftime('%H:%M:%S')}")
    print("-" * 72)
    print(" [STAN GRY]")
    print(f"   Runda/Etap: {info['stage']:<6} | Poziom: {info['level']:<2} (XP: {info['xp']}) | Złoto: {info['gold']}g | HP: {info.get('hp', '??')}")
    print("-" * 72)
    print(" [SKLEP]")
    shop_str = " | ".join([f"[{i+1}] {name if name else '(Pusty)'}" for i, name in enumerate(shop)])
    print(f"   {shop_str}")
    print("-" * 72)
    print(" [PLANSZA - AKTYWNE POSTACIE]")
    
    # Grupowanie postaci według rzędów
    rows = {0: [], 1: [], 2: [], 3: []}
    for hero in board:
        r = hero.get("row", 0)
        c = hero.get("col", 0)
        rows[r].append(f"{hero['champion']} ({r},{c})")
        
    for r in range(4):
        row_name = {3: "Frontline (R3)", 2: "Mid-Front (R2)", 1: "Mid-Back  (R1)", 0: "Backline  (R0)"}[r]
        heroes = ", ".join(rows[r]) if rows[r] else "Pusty"
        print(f"   {row_name:<15} : {heroes}")
        
    print("-" * 72)
    print(" [ŁAWKA REZERWOWYCH]")
    bench_slots = ["(Pusty)"] * 9
    for hero in bench:
        slot = hero.get("slot_id", 0)
        if 0 <= slot < 9:
            bench_slots[slot] = hero["champion"]
    
    bench_str_1 = " | ".join([f"[{i}] {bench_slots[i]}" for i in range(5)])
    bench_str_2 = " | ".join([f"[{i}] {bench_slots[i]}" for i in range(5, 9)])
    print(f"   {bench_str_1}")
    print(f"   {bench_str_2}")
    
    print("-" * 72)
    print(" [PRZEDMIOTY (ŁAWKA)]")
    if items:
        item_list = []
        for i, item in enumerate(items):
            item_name = item.get("item", "Nieznany")
            item_list.append(f"[{i}] {item_name}")
        print(f"   {', '.join(item_list)}")
    else:
        print("   Brak przedmiotów na ławce przedmiotów.")
    print("=" * 72)

def send_state_to_backend(data):
    """
    Placeholder funkcji wysyłającej stan JSON na zewnętrzny serwer sieciowy.
    """
    try:
        # Niski timeout, aby nie blokować pętli głównej (gra działa w czasie rzeczywistym)
        response = requests.post(BACKEND_URL, json=data, timeout=0.2)
        if response.status_code == 200:
            return "WYSŁANO (OK)"
        else:
            return f"BŁĄD (Status {response.status_code})"
    except requests.exceptions.RequestException:
        return "BŁĄD (Brak połączenia z backendem)"

def main():
    print("[Main] Uruchamianie klienta wizji komputerowej TFT...")
    
    # Inicjalizacja komponentów
    capturer = ScreenCapturer(monitor_index=None)
    ocr = OCRProcessor(use_engine="easyocr")
    detector = TFTYoloDetector()
    
    print("[Main] Klient gotowy. Rozpoczynanie pętli głównej...")
    
    try:
        while True:
            start_time = time.time()
            
            # 1. Przechwycenie obrazu z ekranu
            frame = capturer.capture_frame()
            if frame is None:
                print("[Main] Błąd: Nie udało się pobrać klatki ekranu.")
                time.sleep(CAPTURE_INTERVAL)
                continue
                
            # Zapis klatki do kalibracji (jeśli włączona w configu)
            if DEBUG_SAVE_FRAMES:
                capturer.save_debug_image(frame)
                
            # 2. Przetwarzanie OCR (wycinanie ROI i odczyt danych)
            gold_roi = capturer.get_roi_slice(frame, ROI_CONFIG["gold"])
            gold = ocr.get_gold(gold_roi)
            
            level_roi = capturer.get_roi_slice(frame, ROI_CONFIG["level"])
            level = ocr.get_level(level_roi)
            
            xp_roi = capturer.get_roi_slice(frame, ROI_CONFIG["xp"])
            xp = ocr.get_xp(xp_roi)
            
            stage_roi = capturer.get_roi_slice(frame, ROI_CONFIG["stage"])
            stage = ocr.get_stage(stage_roi)
            
            # Odczyt sklepu (5 kart bohaterów)
            shop = []
            for i, roi in enumerate(SHOP_SLOTS_ROI):
                slot_roi = capturer.get_roi_slice(frame, roi)
                champ_name = ocr.get_shop_champion(slot_roi, i)
                shop.append(champ_name)
                
            # 3. Detekcja YOLOv8 (postacie plansza/ławka + przedmioty)
            detections = detector.detect_entities(frame)
            
            # Wyciągnięcie wartości HP z dynamicznie wykrytego boxu YOLO + OCR
            hp_val = 100
            hp_boxes = detections.get("hp_boxes", [])
            if hp_boxes:
                # Wybieramy pudełko z największą pewnością detekcji
                best_hp_box = max(hp_boxes, key=lambda x: x["confidence"])
                x1, y1, x2, y2 = best_hp_box["box"]
                hp_roi = frame[y1:y2, x1:x2]
                if hp_roi is not None and hp_roi.size > 0:
                    hp_val = ocr.get_hp(hp_roi)
            else:
                # Fallback do tradycyjnego ROI jeśli zdefiniowany w configu
                if "player_hp" in ROI_CONFIG:
                    hp_roi = capturer.get_roi_slice(frame, ROI_CONFIG["player_hp"])
                    if hp_roi is not None and hp_roi.size > 0:
                        hp_val = ocr.get_hp(hp_roi)
                        
            # 4. Agregacja danych do ujednoliconego formatu JSON
            game_state = {
                "timestamp": round(time.time(), 3),
                "game_info": {
                    "gold": gold,
                    "level": level,
                    "xp": xp,
                    "stage": stage,
                    "hp": hp_val
                },
                "shop": shop,
                "board": detections["board"],
                "bench": detections["bench"],
                "items": detections["items"]
            }
            
            # Zapis stanu do pliku lokalnego
            try:
                with open("current_state.json", "w", encoding="utf-8") as f:
                    json.dump(game_state, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Main] Błąd zapisu JSON: {e}")
                
            # Wysyłka sieciowa do backendu (placeholder)
            backend_status = send_state_to_backend(game_state)
            
            # Wyświetlenie interfejsu w konsoli
            print_cli_dashboard(game_state, detector.mock_mode, ocr.engine)
            print(f" Status zapisu: Zapisano do current_state.json")
            print(f" Status wysyłki sieciowej: {backend_status}")
            
            # Wyświetlenie okna detekcji (jeśli włączone w konfiguracji)
            if SHOW_DETECTION_WINDOW and "annotated_frame" in detections and detections["annotated_frame"] is not None:
                cv2.imshow("TFT Vision Detector", detections["annotated_frame"])
                cv2.waitKey(1)
            
            # Obliczenie czasu trwania pętli i dynamiczny sleep w celu zachowania równego interwału co 1s
            elapsed = time.time() - start_time
            sleep_time = max(0.0, CAPTURE_INTERVAL - elapsed)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\n[Main] Zatrzymano klienta na żądanie użytkownika. Wyjście...")
    finally:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

if __name__ == "__main__":
    main()
