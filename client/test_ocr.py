import os
import sys
import cv2
import time
from client.config import ROI_CONFIG, SHOP_SLOTS_ROI, DEBUG_DIR
from client.capture import ScreenCapturer
from client.ocr_processor import OCRProcessor

def main():
    # Inicjalizacja silnika OCR z preferencją dla tesseract (lub easyocr)
    engine_choice = "tesseract"
    if len(sys.argv) > 2:
        engine_choice = sys.argv[2]
        
    print(f"=== Uruchamianie testu OCR (silnik: {engine_choice}) ===")
    ocr = OCRProcessor(use_engine=engine_choice)
    print(f"Aktywny silnik OCR: {ocr.engine.upper()}")
    
    # Krok 1: Pobranie obrazu testowego (z pliku lub na żywo z ekranu)
    frame = None
    image_path = None
    
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        image_path = sys.argv[1]
        print(f"Wczytywanie obrazu testowego z pliku: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            print("Błąd: Nie można wczytać podanego obrazu!")
            sys.exit(1)
    else:
        print("Nie podano pliku testowego. Przechwytywanie obrazu na żywo z ekranu...")
        capturer = ScreenCapturer(monitor_index=2)
        # Krótkie opóźnienie, aby dać czas na przełączenie okna gry
        print("Rozpoczynam przechwytywanie za 3 sekundy... (Przełącz na grę)")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
            
        frame = capturer.capture_frame()
        if frame is None:
            print("Błąd: Nie udało się przechwycić klatki ekranu!")
            sys.exit(1)
            
        # Zapisujemy pełną klatkę do debugowania
        if not os.path.exists(DEBUG_DIR):
            os.makedirs(DEBUG_DIR)
        full_frame_path = os.path.join(DEBUG_DIR, "live_test_frame.png")
        cv2.imwrite(full_frame_path, frame)
        print(f"Zapisano przechwyconą klatkę do: {full_frame_path}")

    # Upewniamy się, że katalog debug istnieje
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)

    capturer_utils = ScreenCapturer(monitor_index=2)
    # Jeśli szerokość/wysokość wczytanego obrazu różni się od monitora, zaktualizujmy je w capturerze do skalowania ROI
    if image_path:
        capturer_utils.width = frame.shape[1]
        capturer_utils.height = frame.shape[0]

    print("\n--- Analiza ROI i odczyt OCR ---")
    
    # 1. ZŁOTO
    gold_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["gold"])
    gold_val = ocr.get_gold(gold_roi)
    if gold_roi is not None:
        gold_prep = ocr.preprocess_for_ocr(gold_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_gold.png"), gold_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_gold_thresh.png"), gold_prep)
        
    # 2. LVL
    lvl_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["level"])
    lvl_val = ocr.get_level(lvl_roi)
    if lvl_roi is not None:
        lvl_prep = ocr.preprocess_for_ocr(lvl_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_level.png"), lvl_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_level_thresh.png"), lvl_prep)
        
    # 3. XP
    xp_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["xp"])
    xp_val = ocr.get_xp(xp_roi)
    if xp_roi is not None:
        xp_prep = ocr.preprocess_for_ocr(xp_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_xp.png"), xp_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_xp_thresh.png"), xp_prep)
        
    # 4. ETAP
    stage_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["stage"])
    stage_val = ocr.get_stage(stage_roi)
    if stage_roi is not None:
        stage_prep = ocr.preprocess_for_ocr(stage_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_stage.png"), stage_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_stage_thresh.png"), stage_prep)

    # 5. HP GRACZA
    hp_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["player_hp"])
    hp_val = ocr.get_hp(hp_roi)
    if hp_roi is not None:
        hp_prep = ocr.preprocess_for_ocr(hp_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_player_hp.png"), hp_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_player_hp_thresh.png"), hp_prep)

    # 6. ODSWIEZ
    odswiez_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["odswiez"])
    odswiez_val = ocr.run_ocr(ocr.preprocess_for_ocr(odswiez_roi)) if odswiez_roi is not None else ""
    if odswiez_roi is not None:
        odswiez_prep = ocr.preprocess_for_ocr(odswiez_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_odswiez.png"), odswiez_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_odswiez_thresh.png"), odswiez_prep)

    # 7. PROCENTY
    procenty_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["procenty"])
    procenty_val = ocr.run_ocr(ocr.preprocess_for_ocr(procenty_roi)) if procenty_roi is not None else ""
    if procenty_roi is not None:
        procenty_prep = ocr.preprocess_for_ocr(procenty_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_procenty.png"), procenty_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_procenty_thresh.png"), procenty_prep)

    # 8. MAPA
    mapa_roi = capturer_utils.get_roi_slice(frame, ROI_CONFIG["mapa"])
    mapa_val = ocr.run_ocr(ocr.preprocess_for_ocr(mapa_roi)) if mapa_roi is not None else ""
    if mapa_roi is not None:
        mapa_prep = ocr.preprocess_for_ocr(mapa_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_mapa.png"), mapa_roi)
        cv2.imwrite(os.path.join(DEBUG_DIR, "test_roi_mapa_thresh.png"), mapa_prep)

    # 9. SKLEP
    shop_results = []
    for i, roi in enumerate(SHOP_SLOTS_ROI):
        slot_roi = capturer_utils.get_roi_slice(frame, roi)
        champ_name = ocr.get_shop_champion(slot_roi, i)
        shop_results.append(champ_name)
        if slot_roi is not None:
            slot_prep = ocr.preprocess_for_ocr(slot_roi)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"test_roi_shop_slot_{i+1}.png"), slot_roi)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"test_roi_shop_slot_{i+1}_thresh.png"), slot_prep)

    # Wyniki
    print("\n" + "="*40)
    print("           WYNIKI TESTU OCR")
    print("="*40)
    print(f" ZŁOTO:    {gold_val}")
    print(f" LVL:      {lvl_val}")
    print(f" XP:       {xp_val}")
    print(f" ETAP:     {stage_val}")
    print(f" HP:       {hp_val}")
    print(f" ODSWIEZ:  {odswiez_val}")
    print(f" PROCENTY: {procenty_val}")
    print(f" MAPA:     {mapa_val}")
    print("-" * 40)
    print(" SKLEP (Postaci):")
    for i, name in enumerate(shop_results):
        print(f"   Slot {i+1}: {name if name else '(Pusty / Kupiony)'}")
    print("="*40)
    print(f"\nWycinki ROI oraz ich wersje binarne (progowe) zostały zapisane w katalogu: {DEBUG_DIR}")

if __name__ == "__main__":
    main()
