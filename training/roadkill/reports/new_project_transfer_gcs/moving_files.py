import os
import shutil

def create_subfolders(base_folder):
    subfolders = ['xnx1', 'xnx2']
    for subfolder in subfolders:
        path = os.path.join(base_folder, subfolder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created folder: {path}")

def move_files_to_subfolders(source_folder, target_folder):
    create_subfolders(target_folder)

    for filename in os.listdir(source_folder):
        source_path = os.path.join(source_folder, filename)

        if os.path.isfile(source_path):
            if 'xnx1' in filename:
                target_path = os.path.join(target_folder, 'xnx1', filename)
            elif 'xnx2' in filename:
                target_path = os.path.join(target_folder, 'xnx2', filename)
            else:
                continue 

            shutil.move(source_path, target_path)
            print(f"Moved {filename} to {target_path}")

if __name__ == "__main__":
    source_folder = '/Users/aleksandra/Desktop/images2' 
    target_folder = '/Users/aleksandra/Desktop/images' 

    move_files_to_subfolders(source_folder, target_folder)
