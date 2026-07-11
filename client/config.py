import os

# Podstawowa rozdzielczość, dla której zdefiniowano ROI (Region of Interest)
BASE_RESOLUTION = (1920, 1080)

# Indeks monitora do przechwytywania (0 dla wszystkich połączonych ekranów, 1 dla głównego, 2 dla pomocniczego itd.)
MONITOR_INDEX = 1

# Częstotliwość próbkowania (w sekundach)
CAPTURE_INTERVAL = 1.0

# Ścieżka do modelu YOLOv8. Jeśli plik nie istnieje, system automatycznie przejdzie w tryb symulacji (MOCK_MODE)
YOLO_MODEL_PATH = "yolov8n_tft.pt"
CONFIDENCE_THRESHOLD = 0.45

# Adres URL backendu, do którego będą wysyłane dane JSON
BACKEND_URL = "http://localhost:5000/api/tft/state"

# Zapisywanie zrzutów ekranu do folderu debugowania w celu kalibracji ROI
DEBUG_SAVE_FRAMES = False
SHOW_DETECTION_WINDOW = True
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG_DIR = os.path.join(PROJECT_ROOT, "debug")

# Ścieżka do pliku wykonywalnego Tesseract-OCR na Windows (opcjonalne, jeśli nie ma w PATH)
# Przykład: TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

# Definicje obszarów (ROI) w rozdzielczości 1920x1080.
# Format: { "top": y_poczatek, "left": x_poczatek, "width": szerokosc, "height": wysokosc }
ROI_CONFIG = {
    "gold": {"top": 878, "left": 957, "width": 32, "height": 26},         # ZLOTO
    "level": {"top": 881, "left": 321, "width": 26, "height": 24},      # LVL
    "xp": {"top": 891, "left": 419, "width": 27, "height": 19},         # Odczyt XP z tego samego obszaru LVL
    "stage": {"top": 3, "left": 700, "width": 32, "height": 34},           # ETAP
    "odswiez": {"top": 996, "left": 270, "width": 196, "height": 80},     # ODSWIEZ
    "procenty": {"top": 883, "left": 472, "width": 298, "height": 30},     # PROCENTY
    "player_hp": {"top": 815, "left": 1825, "width": 35, "height": 22},   # HP fallback
    "mapa": {"top": 800, "left": 1700, "width": 200, "height": 200}        # MAPA fallback
}

# Obszary kart bohaterów w sklepie (tekst z nazwami bohaterów)
# Sklep składa się z 5 kart ułożonych obok siebie na dole ekranu
SHOP_SLOTS_ROI = [
    {"top": 1034, "left": 481, "width": 128, "height": 32},   # KAFELEK1
    {"top": 1040, "left": 686, "width": 122, "height": 28},   # KAFELEK2
    {"top": 1038, "left": 885, "width": 118, "height": 25},   # KAFELEK3
    {"top": 1037, "left": 1088, "width": 141, "height": 35},  # KAFELEK4
    {"top": 1037, "left": 1289, "width": 132, "height": 36}   # KAFELEK5
]

# Definicja punktów narożnych trapezoidu planszy do transformacji perspektywicznej (3D -> 2D Grid)
# Punkty odpowiadają narożnikom aktywnego pola gry (4 rzędy po 7 heksów):
# [Lewy Górny, Prawy Górny, Prawy Dolny, Lewy Dolny] w rozdzielczości 1920x1080.
BOARD_CORNER_POINTS = [
    (669, 311),   # Lewy Górny (narożnik przy linii środkowej gry, zwężenie perspektywy)
    (1310, 311),  # Prawy Górny
    (1530, 664),  # Prawy Dolny (przy ławce rezerwowych)
    (449, 664)    # Lewy Dolny
]

# Współrzędne ławki rezerwowych (9 slotów liniowo)
BENCH_REGION = {
    "x_min": 359,
    "x_max": 1439,
    "y_min": 706,
    "y_max": 840
}

# Współrzędne obszaru na przedmioty (po lewej stronie planszy)
ITEM_BENCH_REGION = {
    "x_min": 0,
    "x_max": 96,
    "y_min": 232,
    "y_max": 822
}

# Funkcja pomocnicza do automatycznego skalowania ROI w zależności od rozdzielczości gry
def scale_roi(roi, current_res):
    """
    Skaluje prostokątny ROI z rozdzielczości bazowej 1920x1080 do aktualnej rozdzielczości ekranu.
    roi: Słownik {"left": ..., "top": ..., "width": ..., "height": ...}
    current_res: Tuple (width, height)
    """
    base_w, base_h = BASE_RESOLUTION
    curr_w, curr_h = current_res
    
    if (base_w, base_h) == (curr_w, curr_h):
        return roi
        
    scale_x = curr_w / base_w
    scale_y = curr_h / base_h
    
    return {
        "left": int(roi["left"] * scale_x),
        "top": int(roi["top"] * scale_y),
        "width": int(roi["width"] * scale_x),
        "height": int(roi["height"] * scale_y)
    }

def scale_point(point, current_res):
    """
    Skaluje pojedynczy punkt (x, y) z rozdzielczości bazowej 1920x1080 do aktualnej rozdzielczości.
    """
    base_w, base_h = BASE_RESOLUTION
    curr_w, curr_h = current_res
    
    if (base_w, base_h) == (curr_w, curr_h):
        return point
        
    scale_x = curr_w / base_w
    scale_y = curr_h / base_h
    
    return (int(point[0] * scale_x), int(point[1] * scale_y))
