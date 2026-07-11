import os
import shutil

def split_folder_into_batches(target_dir, batch_size=99):
    """
    Dzieli pliki w wybranym folderze na podfoldery zawierające po max `batch_size` plików.
    """
    if not os.path.exists(target_dir):
        print(f"BŁĄD: Folder '{target_dir}' nie istnieje!")
        return

    # Pobieramy listę wszystkich plików w folderze (ignorując już istniejące podfoldery)
    files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    
    # Sortujemy pliki, aby zachować chronologię klatek
    files.sort()
    
    total_files = len(files)
    if total_files == 0:
        print(f"Brak plików do podziału w folderze: {target_dir}")
        return

    print(f"Znaleziono {total_files} plików do podziału w folderze: {target_dir}")
    print(f"Rozmiar paczki: {batch_size} plików na folder.")
    
    batch_num = 1
    for i in range(0, total_files, batch_size):
        # Pobieramy wycinek plików dla bieżącej paczki
        batch_files = files[i:i + batch_size]
        
        # Nazwa nowego podfolderu
        batch_folder_name = f"part_{batch_num}"
        batch_folder_path = os.path.join(target_dir, batch_folder_name)
        
        # Tworzymy podfolder
        os.makedirs(batch_folder_path, exist_ok=True)
        
        # Przenosimy pliki
        for file_name in batch_files:
            src_path = os.path.join(target_dir, file_name)
            dst_path = os.path.join(batch_folder_path, file_name)
            shutil.move(src_path, dst_path)
            
        print(f" -> Utworzono {batch_folder_name} i przeniesiono {len(batch_files)} plików.")
        batch_num += 1

    print("\nGotowe! Podział zakończony sukcesem.")

if __name__ == "__main__":
    # Ścieżka do folderu z Twoimi pociętymi klatkami
    folder_do_podzialu = r"C:\Users\diabl\Documents\yolo\vid\pocietevid"
    
    split_folder_into_batches(folder_do_podzialu, batch_size=99)
