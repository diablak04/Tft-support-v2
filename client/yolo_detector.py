import os
import random
import cv2
import numpy as np
from client.config import (
    YOLO_MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    BOARD_CORNER_POINTS,
    BENCH_REGION,
    ITEM_BENCH_REGION,
    scale_point
)

class TFTYoloDetector:
    def __init__(self):
        """
        Inicjalizacja modułu YOLOv8 do detekcji postaci oraz przedmiotów.
        W przypadku braku modelu przechodzi w tryb symulacji (MOCK).
        """
        self.mock_mode = True
        self.model = None
        
        # Sprawdzenie obecności pliku modelu
        if os.path.exists(YOLO_MODEL_PATH):
            try:
                from ultralytics import YOLO
                print(f"[TFTYoloDetector] Ładowanie modelu YOLOv8 ze ścieżki: {YOLO_MODEL_PATH}")
                self.model = YOLO(YOLO_MODEL_PATH)
                self.mock_mode = False
                print("[TFTYoloDetector] Model załadowany pomyślnie.")
            except Exception as e:
                print(f"[TFTYoloDetector] Błąd podczas ładowania modelu: {e}")
                print("[TFTYoloDetector] Przełączanie w tryb MOCK...")
        else:
            print(f"[TFTYoloDetector] Brak pliku modelu: {YOLO_MODEL_PATH}")
            print("[TFTYoloDetector] Praca w trybie MOCK (Symulacja detekcji).")

        # Inicjalizacja macierzy transformacji perspektywicznej planszy (Homografia)
        # Cel: Rzutowanie punktów 2D z obrazu na znormalizowaną siatkę planszy o wymiarach 700x400 pikseli.
        # Reprezentuje to 4 rzędy po 7 heksów (każdy heks ma wymiary ok. 100x100 pikseli w tej przestrzeni).
        self.grid_width = 700
        self.grid_height = 400
        
        src_pts = np.float32(BOARD_CORNER_POINTS)
        dst_pts = np.float32([
            [0, 0],                            # Lewy Górny
            [self.grid_width, 0],              # Prawy Górny
            [self.grid_width, self.grid_height],# Prawy Dolny
            [0, self.grid_height]              # Lewy Dolny
        ])
        
        # Obliczenie macierzy perspektywy M
        self.M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    def detect_entities(self, frame):
        """
        Główna funkcja detekcji. Zwraca listę wykrytych obiektów na planszy, ławce i przedmiotów,
        wraz z klatką z naniesionymi wizualizacjami (annotated_frame).
        """
        if frame is None:
            return {"board": [], "bench": [], "items": [], "hp_boxes": [], "annotated_frame": None}
            
        h, w = frame.shape[:2]
        current_res = (w, h)
        
        # Obliczenie współrzędnych obszarów
        scaled_corners = [scale_point(pt, current_res) for pt in BOARD_CORNER_POINTS]
        board_polygon = np.array(scaled_corners, dtype=np.int32)
        
        scaled_bench = {
            "x_min": int(BENCH_REGION["x_min"] * (w / 1920)),
            "x_max": int(BENCH_REGION["x_max"] * (w / 1920)),
            "y_min": int(BENCH_REGION["y_min"] * (h / 1080)),
            "y_max": int(BENCH_REGION["y_max"] * (h / 1080))
        }
        
        scaled_item_bench = {
            "x_min": int(ITEM_BENCH_REGION["x_min"] * (w / 1920)),
            "x_max": int(ITEM_BENCH_REGION["x_max"] * (w / 1920)),
            "y_min": int(ITEM_BENCH_REGION["y_min"] * (h / 1080)),
            "y_max": int(ITEM_BENCH_REGION["y_max"] * (h / 1080))
        }
        
        if self.mock_mode:
            mock_res = self._generate_mock_detections()
            mock_res["hp_boxes"] = []
            
            # Kopia klatki dla wizualizacji mocka
            annotated_frame = frame.copy()
            
            # Rysujemy obszary kalibracji
            cv2.polylines(annotated_frame, [board_polygon], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.rectangle(annotated_frame, (scaled_bench["x_min"], scaled_bench["y_min"]), (scaled_bench["x_max"], scaled_bench["y_max"]), (0, 0, 255), 2)
            cv2.rectangle(annotated_frame, (scaled_item_bench["x_min"], scaled_item_bench["y_min"]), (scaled_item_bench["x_max"], scaled_item_bench["y_max"]), (255, 255, 0), 2)
            
            # Nakładka tekstowa o trybie mock
            cv2.putText(annotated_frame, "TRYB SYMULACJI (MOCK MODE) - YOLO NIEAKTYWNY", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(annotated_frame, "Zielona linia: Plansza (Board)", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(annotated_frame, "Czerwona linia: Lawka (Bench)", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(annotated_frame, "Zolta linia: Przedmioty (Item Bench)", (30, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Rysowanie fikcyjnych jednostek z mocka
            for hero in mock_res["board"]:
                cv2.putText(annotated_frame, f"[Mock Board] {hero['champion']} ({hero['hex']})", 
                            (w // 2 - 120, 200 + hero['row'] * 60 + hero['col'] * 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
            for hero in mock_res["bench"]:
                cv2.putText(annotated_frame, f"[Mock Bench] {hero['champion']} s{hero['slot_id']}", 
                            (scaled_bench["x_min"] + hero['slot_id'] * 110, scaled_bench["y_min"] + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                            
            for item in mock_res["items"]:
                cv2.putText(annotated_frame, f"[Mock Item] {item['item']}", 
                            (scaled_item_bench["x_min"] + 10, scaled_item_bench["y_min"] + 60 + item['slot_id'] * 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
                            
            mock_res["annotated_frame"] = annotated_frame
            return mock_res
            
        # Uruchomienie detekcji modelu YOLO (TRYB REALNY)
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        detections = results[0]
        
        # Wbudowane rysowanie ramek i nazw klas przez YOLO
        annotated_frame = detections.plot()
        
        # Rysujemy geometryczne obszary kalibracji (plansza, ławka, przedmioty)
        cv2.polylines(annotated_frame, [board_polygon], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.rectangle(annotated_frame, (scaled_bench["x_min"], scaled_bench["y_min"]), (scaled_bench["x_max"], scaled_bench["y_max"]), (0, 0, 255), 2)
        cv2.rectangle(annotated_frame, (scaled_item_bench["x_min"], scaled_item_bench["y_min"]), (scaled_item_bench["x_max"], scaled_item_bench["y_max"]), (255, 255, 0), 2)
        
        board_entities = []
        bench_entities = []
        item_entities = []
        hp_boxes = []
        
        # Obliczenie lokalnej homografii dla aktualnej rozdzielczości
        src_pts = np.float32(scaled_corners)
        dst_pts = np.float32([
            [0, 0],
            [self.grid_width, 0],
            [self.grid_width, self.grid_height],
            [0, self.grid_height]
        ])
        local_M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Zdefiniowane klasy przedmiotów w modelu
        ITEM_CLASSES = {
            "BF_Sword", "Chain_Vest", "Frying_Pan", "Giants_Belt", "Needlessly_Large_Rod",
            "Negatron_Cloak", "Recurve_Bow", "Sparring_Gloves", "Spatula", "Tear_of_the_Goddess"
        }
        
        # Odczyt słowników klas z modelu
        names = self.model.names
        
        for box in detections.boxes:
            # Pobranie współrzędnych i klasy detekcji
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = names.get(cls_id, f"class_{cls_id}")
            
            # Środek boxu (często lepszy dla przedmiotów/HP)
            cx_center = (x1 + x2) // 2
            cy_center = (y1 + y2) // 2
            
            # Punkt stóp postaci (środek dolnej krawędzi boxu) jest najlepszym przybliżeniem pozycji 3D na planszy
            cx_feet = (x1 + x2) // 2
            cy_feet = y2
            
            # Obsługa klasy HP
            if class_name == "hp":
                hp_boxes.append({
                    "box": (x1, y1, x2, y2),
                    "confidence": round(conf, 2)
                })
                # Opcjonalne zaznaczenie HP na ekranie
                cv2.putText(annotated_frame, "HP Box", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                continue
                
            # Obsługa klas przedmiotów na ławce przedmiotów (po lewej stronie ekranu)
            if class_name in ITEM_CLASSES:
                if (scaled_item_bench["x_min"] <= cx_center <= scaled_item_bench["x_max"]) and (scaled_item_bench["y_min"] <= cy_center <= scaled_item_bench["y_max"]):
                    # Obliczenie slot_id przedmiotu (0-9) na podstawie osi Y
                    relative_y = cy_center - scaled_item_bench["y_min"]
                    bench_h = scaled_item_bench["y_max"] - scaled_item_bench["y_min"]
                    slot_id = int((relative_y / bench_h) * 10) if bench_h > 0 else 0
                    slot_id = max(0, min(slot_id, 9))
                    
                    item_entities.append({
                        "item": class_name,
                        "slot_id": slot_id,
                        "x": cx_center,
                        "y": cy_center,
                        "confidence": round(conf, 2)
                    })
                    # Zaznaczenie slotu przedmiotu na obrazie
                    cv2.circle(annotated_frame, (cx_center, cy_center), 4, (255, 255, 0), -1)
                    cv2.putText(annotated_frame, f"slot {slot_id}", (cx_center - 20, cy_center - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                continue
                
            # Jeśli to nie jest HP ani Przedmiot, traktujemy jako bohatera (championa)
            # 1. Sprawdzenie czy punkt stóp należy do planszy
            is_on_board = cv2.pointPolygonTest(board_polygon, (float(cx_feet), float(cy_feet)), False) >= 0
            
            if is_on_board:
                # Rzutowanie punktu 2D na współrzędne siatki 700x400
                pt = np.array([[[cx_feet, cy_feet]]], dtype=np.float32)
                transformed_pt = cv2.perspectiveTransform(pt, local_M)
                tx, ty = transformed_pt[0][0]
                
                # Przeliczenie na rzędy (0-3) i kolumny (0-6)
                col = int(tx // 100)
                row = int(ty // 100)
                
                # Zabezpieczenie przed wyjściem poza indeksy siatki
                col = max(0, min(col, 6))
                row = max(0, min(row, 3))
                
                board_entities.append({
                    "champion": class_name,
                    "hex": f"r{row}_c{col}",
                    "row": row,
                    "col": col,
                    "confidence": round(conf, 2)
                })
                # Zaznaczenie punktu rzutowania stóp i pozycji hex
                cv2.circle(annotated_frame, (cx_feet, cy_feet), 5, (0, 255, 0), -1)
                cv2.putText(annotated_frame, f"r{row}_c{col}", (cx_feet - 15, cy_feet - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                continue
                
            # 2. Sprawdzenie czy należy do ławki rezerwowych
            if (scaled_bench["x_min"] <= cx_feet <= scaled_bench["x_max"]) and (scaled_bench["y_min"] <= cy_feet <= scaled_bench["y_max"]):
                # Obliczenie indeksu slotu ławki (0-8)
                bench_w = scaled_bench["x_max"] - scaled_bench["x_min"]
                relative_x = cx_feet - scaled_bench["x_min"]
                slot_id = int((relative_x / bench_w) * 9) if bench_w > 0 else 0
                slot_id = max(0, min(slot_id, 8))
                
                bench_entities.append({
                    "champion": class_name,
                    "slot_id": slot_id,
                    "confidence": round(conf, 2)
                })
                # Zaznaczenie punktu rzutowania stóp i slotu ławki
                cv2.circle(annotated_frame, (cx_feet, cy_feet), 5, (0, 0, 255), -1)
                cv2.putText(annotated_frame, f"slot {slot_id}", (cx_feet - 15, cy_feet - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                
        return {
            "board": board_entities,
            "bench": bench_entities,
            "items": item_entities,
            "hp_boxes": hp_boxes,
            "annotated_frame": annotated_frame
        }
                


    def _generate_mock_detections(self):
        """
        Generuje realistyczne symulowane detekcje (tryb MOCK).
        Symuluje standardowy mid-game board z kilkoma postaciami.
        """
        board = [
            {"champion": "Yasuo", "hex": "r2_c3", "row": 2, "col": 3, "stars": 2, "confidence": 0.94},
            {"champion": "Aatrox", "hex": "r3_c2", "row": 3, "col": 2, "stars": 2, "confidence": 0.89},
            {"champion": "Bard", "hex": "r0_c3", "row": 0, "col": 3, "stars": 2, "confidence": 0.91},
            {"champion": "Lillia", "hex": "r0_c4", "row": 0, "col": 4, "stars": 1, "confidence": 0.88}
        ]
        
        bench = [
            {"champion": "Yasuo", "slot_id": 0, "confidence": 0.92},
            {"champion": "Tahm Kench", "slot_id": 3, "confidence": 0.85}
        ]
        
        items = [
            {"item": "Infinity_Edge", "slot_id": 0, "confidence": 0.96},
            {"item": "BF_Sword", "slot_id": 1, "confidence": 0.90}
        ]
        
        # Drobna losowość, aby symulować zmieniający się stan
        if random.random() < 0.1:
            # Czasami dodaj postać na benchu
            bench.append({"champion": "Yone", "slot_id": 5, "confidence": 0.79})
            
        return {
            "board": board,
            "bench": bench,
            "items": items
        }
