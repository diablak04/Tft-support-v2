import re
import cv2
import numpy as np

# Próba importu silników OCR
EASYOCR_AVAILABLE = False
TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract
    from client.config import TESSERACT_CMD
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    TESSERACT_AVAILABLE = True
except ImportError:
    pass

class OCRProcessor:
    def __init__(self, use_engine="easyocr"):
        """
        Inicjalizacja modułu OCR.
        use_engine: "easyocr" lub "tesseract". W przypadku braku instalacji, nastąpi automatyczny fallback.
        """
        self.engine = None
        
        if use_engine == "easyocr" and EASYOCR_AVAILABLE:
            print("[OCRProcessor] Inicjalizacja EasyOCR...")
            # Inicjalizujemy model dla języka angielskiego (TFT używa głównie angielskich nazw i cyfr)
            self.reader = easyocr.Reader(['en'], gpu=False) # GPU=False by zapobiec nadmiernemu zużyciu VRAM (Vanguard/gra potrzebują GPU)
            self.engine = "easyocr"
            print("[OCRProcessor] EasyOCR gotowy.")
        elif TESSERACT_AVAILABLE:
            print("[OCRProcessor] Pytesseract wykryty. Używanie Tesseract OCR.")
            self.engine = "tesseract"
        else:
            print("[OCRProcessor] OSTRZEŻENIE: Brak zainstalowanego EasyOCR oraz PyTesseract!")
            print("[OCRProcessor] Program uruchomi się w trybie symulacji OCR (MOCK).")
            print("[OCRProcessor] Aby włączyć prawdziwy OCR, zainstaluj: pip install easyocr")
            self.engine = "mock"

    def preprocess_for_ocr(self, roi_image):
        """
        Wstępne przetwarzanie obrazu za pomocą OpenCV w celu poprawy jakości odczytu OCR.
        - Konwersja do skali szarości.
        - Powiększenie obrazu (2x) za pomocą interpolacji sześciennej (ułatwia odczyt małych czcionek).
        - Progowanie binarne Otsu.
        """
        if roi_image is None or roi_image.size == 0:
            return None
            
        # 1. Konwersja do odcieni szarości
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
        
        # 2. Skalowanie w górę (2x) - przydatne dla małych tekstów jak Gold czy HP
        resized = cv2.resize(gray, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        
        # 3. Progowanie (Thresholding) w celu wyciągnięcia czystego białego tekstu na ciemnym tle
        _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh

    def run_ocr(self, processed_img):
        """
        Uruchamia wybrany silnik OCR na przetworzonym obrazie.
        """
        if processed_img is None:
            return ""
            
        if self.engine == "easyocr":
            # EasyOCR wymaga tablicy numpy. Zwraca listę krotek: (bbox, text, confidence)
            results = self.reader.readtext(processed_img)
            texts = [res[1] for res in results]
            return " ".join(texts).strip()
            
        elif self.engine == "tesseract":
            # Tesseract
            try:
                config = '--psm 7' # PSM 7: traktuj obraz jako pojedynczą linię tekstu
                text = pytesseract.image_to_string(processed_img, config=config)
                return text.strip()
            except Exception as e:
                print(f"[OCRProcessor] Błąd Tesseract OCR (prawdopodobnie brak zainstalowanego programu Tesseract w systemie): {e}")
                print("[OCRProcessor] Przełączam automatycznie na tryb symulacji (MOCK), aby uniknąć błędu.")
                self.engine = "mock"
                return ""
            
        else:
            # Tryb MOCK - symulacja braku silnika OCR
            return None

    def get_gold(self, roi_image):
        """
        Odczytuje ilość złota. Oczekuje liczby całkowitej.
        """
        if self.engine == "mock":
            # Zwracamy przykładowe złoto
            return 48
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        # Odfiltrowanie tylko cyfr
        digits = re.sub(r"\D", "", text)
        if digits:
            return int(digits)
        return 0

    def get_level(self, roi_image):
        """
        Odczytuje poziom gracza.
        """
        if self.engine == "mock":
            return 8
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        # Wyciągamy cyfry (np. "Lvl. 8" -> 8)
        digits = re.sub(r"\D", "", text)
        if digits:
            return int(digits)
        return 1

    def get_xp(self, roi_image):
        """
        Odczytuje stan XP (np. "42/56").
        """
        if self.engine == "mock":
            return "42/56"
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        # Szukamy wzorca cyfra/cyfra
        match = re.search(r"(\d+)\s*/\s*(\d+)", text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
            
        # Zastępcze wyszukiwanie cyfr, jeśli ukośnik nie został wykryty
        digits = re.findall(r"\d+", text)
        if len(digits) >= 2:
            return f"{digits[0]}/{digits[1]}"
        elif len(digits) == 1:
            return f"{digits[0]}/??"
            
        return "0/4"

    def get_stage(self, roi_image):
        """
        Odczytuje aktualny etap (Stage/Round, np. "3-2").
        """
        if self.engine == "mock":
            return "3-2"
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        # Szukamy formatu "cyfra-cyfra" (np. "3-2", "4-1")
        match = re.search(r"(\d+)\s*[-_—]\s*(\d+)", text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return "1-1"

    def get_hp(self, roi_image):
        """
        Odczytuje HP gracza.
        """
        if self.engine == "mock":
            return 82
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        digits = re.sub(r"\D", "", text)
        if digits:
            hp = int(digits)
            # HP gracza w TFT to maksymalnie 100 (lub lekko więcej z niektórymi ulepszeniami)
            return min(hp, 150)
        return 100

    def get_shop_champion(self, roi_image, slot_index):
        """
        Odczytuje nazwę bohatera ze slotu sklepu.
        """
        if self.engine == "mock":
            mock_champions = ["Tristana", "Tahm Kench", "Bard", "Lillia", "Yone"]
            return mock_champions[slot_index]
            
        processed = self.preprocess_for_ocr(roi_image)
        text = self.run_ocr(processed)
        
        # Filtrujemy znaki nie-alfabetyczne, zostawiamy litery i spacje (np. "Tahm Kench")
        cleaned_text = re.sub(r"[^a-zA-Z\s]", "", text).strip()
        
        # Jeśli tekst jest zbyt krótki, prawdopodobnie slot jest pusty (kupiony bohater)
        if len(cleaned_text) < 3:
            return ""
            
        # Zapewnienie wielkiej litery na początku wyrazu
        words = [w.capitalize() for w in cleaned_text.split()]
        return " ".join(words)
