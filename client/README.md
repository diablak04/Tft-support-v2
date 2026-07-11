# Klient Wizji Komputerowej dla Asystenta TFT (Komputer #3)

Ten projekt to lokalny klient wizji komputerowej dedykowany dla gry **Teamfight Tactics (TFT)**. Program działa na komputerze gracza (Komputer nr 3), analizując obraz z gry w czasie rzeczywistym (co 1.0s) przy użyciu algorytmów OCR oraz sieci YOLOv8. Wszystkie pozyskane informacje są strukturyzowane do formatu JSON i zapisywane lokalnie oraz przygotowane do przesyłania na zewnętrzny backend.

---

## 🛡️ Bezpieczeństwo i Kompatybilność z Anti-Cheatem (Riot Vanguard)

Projekt został zaprojektowany z myślą o pełnej pasywności i zgodności z Riot Vanguard. Jako gracze rangi Challenger doskonale wiemy, jak restrykcyjny jest system Vanguard, dlatego klient spełnia następujące warunki bezpieczeństwa:

1. **Praca wyłącznie w przestrzeni użytkownika (User-Space)**: Program nie instaluje żadnych sterowników systemowych, nie działa na poziomie jądra systemu (Ring 0) ani nie wymaga uprawnień administratora do przechwytywania.
2. **Całkowity brak ingerencji w grę**:
   - **Brak odczytu pamięci RAM (No Memory Reading)**: Klient w ogóle nie analizuje pamięci procesu `League of Legends.exe`.
   - **Brak DLL Injection / API Hooking**: Nie modyfikujemy kodu gry ani nie podpinamy się pod silnik graficzny (DirectX/Vulkan).
3. **Pasywność (No Automation/Inputs)**: Program nie wykonuje żadnych automatycznych kliknięć, ruchów myszą ani symulacji klawiatury. Jest wyłącznie pasywnym obserwatorem ekranu.
4. **Bezpieczne systemowe API**: Pobieranie obrazu odbywa się za pomocą biblioteki `mss`, która wykonuje standardowe zrzuty ekranu poprzez API systemu operacyjnego (identycznie jak OBS Studio czy Discord).

---

## 📁 Struktura Projektu

Katalog `client/` zawiera następujące moduły:

- `config.py` — parametry konfiguracyjne, współrzędne ROI (Region of Interest) w rozdzielczości 1920x1080, współrzędne siatki planszy oraz funkcje skalujące ROI.
- `capture.py` — moduł przechwytywania ekranu wykorzystujący bibliotekę `mss` z obsługą skalowania i wycinania ROI.
- `ocr_processor.py` — moduł filtrowania obrazu OpenCV (szarość, powiększenie, progowanie Otsu) i odczytywania wartości tekstowych (Złoto, HP, Poziom, XP, Sklep) przy użyciu EasyOCR / PyTesseract.
- `yolo_detector.py` — moduł YOLOv8 (Ultralytics) wykrywający postacie i przedmioty na planszy oraz ławce rezerwowych. Zaimplementowano rzutowanie perspektywiczne 3D -> 2D (Homografia) na siatkę 28 heksów planszy.
- `main.py` — pętla główna integrująca wszystkie moduły, uruchamiająca analizę co 1.0s, generująca CLI dashboard, zapisująca stan do `current_state.json` oraz wysyłająca dane przez POST.
- `requirements.txt` — lista zależności Pythona.

---

## 🚀 Instalacja i Uruchomienie

Projekt został przygotowany w oparciu o istniejące środowisko wirtualne `.venv` w katalogu roboczym.

### 1. Aktywacja środowiska i instalacja zależności
Otwórz terminal PowerShell w głównym katalogu projektu i wykonaj:

```powershell
# Aktywacja środowiska wirtualnego
.\.venv\Scripts\Activate.ps1

# Instalacja brakujących pakietów (np. EasyOCR)
pip install -r client/requirements.txt
```

### 2. Uruchomienie Klienta
```powershell
python -m client.main
```
*Uwaga: Jeśli nie masz wgranej sieci YOLOv8 (`yolov8n_tft.pt`) lub zainstalowanych silników OCR na systemie, program automatycznie przełączy się w **tryb symulacji (MOCK)**, dzięki czemu możesz od razu przetestować pętlę i strukturę wyjściową JSON.*

---

## 🎯 Instrukcja Kalibracji ROI (Region of Interest)

Domyślne koordynaty ROI w `config.py` są zoptymalizowane pod rozdzielczość **1920x1080 (FullHD)** przy standardowym interfejsie TFT. Jeśli grasz w innej rozdzielczości lub zmieniłeś skalowanie HUD w grze, musisz przeprowadzić kalibrację:

1. W pliku `client/config.py` ustaw flagę `DEBUG_SAVE_FRAMES = True`.
2. Uruchom grę TFT (w oknie bez ramek - *Borderless*) i włącz klienta komendą `python -m client.main`.
3. Klient zacznie zapisywać zrzuty ekranu do folderu `debug_captures/`. Wyłącz program po wykonaniu kilku klatek (`Ctrl + C`).
4. Otwórz wybrany zrzut ekranu w darmowym edytorze graficznym (np. Paint, GIMP, Photoshop).
5. Odczytaj współrzędne pikseli (lewy górny róg oraz prawy dolny róg) dla interesujących Cię elementów:
   - **Gold** (Złoto na dole ekranu)
   - **Level** (Poziom gracza na dole po lewej)
   - **XP** (Wartość XP obok poziomu)
   - **Stage** (Etap gry na górze ekranu)
   - **HP** (Wskaźnik HP gracza po prawej stronie)
   - **Karty w sklepie** (5 prostokątów z nazwami bohaterów)
6. Zaktualizuj współrzędne w słownikach `ROI_CONFIG` oraz `SHOP_SLOTS_ROI` w pliku `client/config.py`.
7. Przywróć ustawienie `DEBUG_SAVE_FRAMES = False` w konfiguracji.

---

## 🧠 Trening Własnego Modelu YOLOv8 (Ultralytics)

Jeśli chcesz przejść z trybu symulacji (MOCK) na autentyczne wykrywanie postaci na planszy, musisz wytrenować własny model YOLOv8:

### Krok 1: Zbieranie i etykietowanie danych (Dataset)
1. Zbierz zrzuty ekranu z rozgrywki TFT (np. używając modułu debugowania w `capture.py`). Zbierz około 200-500 obrazów zawierających różne postacie i przedmioty.
2. Zarejestruj się na platformie **Roboflow** (roboflow.com) lub użyj lokalnego narzędzia **CVAT**.
3. Zaimportuj zdjęcia i oznacz bounding boxy:
   - Klasy postaci (np. `champion` lub nazwy konkretnych jednostek, jeśli chcesz rozróżniać klasy bezpośrednio).
   - Klasy gwiazdek (np. `1_star`, `2_star`, `3_star` nad postaciami).
   - Klasy przedmiotów (np. `Infinity_Edge`, `Warmogs`, itp.).
4. Wyeksportuj zbiór danych w formacie **YOLOv8 PyTorch**.

### Krok 2: Instalacja narzędzi treningowych i Trening
Uruchom trening przy użyciu biblioteki `ultralytics` w terminalu:

```powershell
# Uruchomienie treningu YOLOv8 Nano (szybkiej sieci idealnej do czasu rzeczywistego)
yolo task=detect mode=train model=yolov8n.pt data=sciezka/do/dataset.yaml epochs=100 imgsz=640 device=0
```
*Uwaga: Parametr `device=0` wymusza użycie karty graficznej NVIDIA (CUDA). Upewnij się, że masz zainstalowane CUDA Toolkit.*

### Krok 3: Integracja modelu z Klientem
1. Po zakończeniu treningu, plik wag twojego modelu znajdziesz w: `runs/detect/train/weights/best.pt`.
2. Skopiuj ten plik do głównego folderu projektu.
3. Zmień jego nazwę na `yolov8n_tft.pt`.
4. Klient automatycznie wykryje model przy następnym uruchomieniu i wyłączy tryb symulacji (MOCK).
