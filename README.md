# TFT Asystent V2 (TFT-support-v2)

Ten projekt to asystent wspomagający rozgrywkę w Teamfight Tactics (TFT) za pomocą analizy obrazu w czasie rzeczywistym.

## 📁 Struktura projektu

Projekt składa się z następujących głównych komponentów:

* **[client/](file:///c:/Users/diabl/Documents/antigravity/Tft-support-v2/client)** — Główny moduł klienta gry napisany w Pythonie (przechwytywanie ekranu za pomocą `mss`, przetwarzanie tekstu OCR oraz detekcja postaci/przedmiotów na planszy/ławce przy użyciu YOLOv8).
* **[yolov8n_tft.pt](file:///c:/Users/diabl/Documents/antigravity/Tft-support-v2/yolov8n_tft.pt)** — Wytrenowany model YOLOv8 (wagi sieci) używany do detekcji postaci oraz przedmiotów.
* **[slice_video.py](file:///c:/Users/diabl/Documents/antigravity/Tft-support-v2/slice_video.py)** — Skrypt pomocniczy do cięcia nagrań wideo (.mp4, .mkv itp.) na klatki JPG w celu przygotowania zbioru danych (datasetu).
* **[split_folder.py](file:///c:/Users/diabl/Documents/antigravity/Tft-support-v2/split_folder.py)** — Skrypt pomocniczy do dzielenia zdjęć z klatkami na mniejsze foldery/paczki (np. po 99 plików) ułatwiający tagowanie w programach takich jak AnyLabeling.

## 🚀 Szybki start i Konfiguracja

Instrukcja instalacji środowiska wirtualnego, instalacja zależności, kalibracja ROI (współrzędnych interfejsu gry) oraz uruchomienie klienta znajdują się w pliku:
👉 **[Instrukcja w client/README.md](file:///c:/Users/diabl/Documents/antigravity/Tft-support-v2/client/README.md)**
