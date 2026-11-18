import os

#change names of files based on .txt file with two columns - the old names and the new names

def rename_files_from_txt(file_path: str, folder_path: str, delimiter=','):
    if not os.path.isdir(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    # read the .txt file
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(delimiter)
                if len(parts) < 2:
                    continue  

                old_name_base, new_name_base = parts[0].strip(), parts[1].strip()
                if old_name_base.endswith('.json'):
                    old_name_base = old_name_base[:-5]
                if new_name_base.endswith('.json'):
                    new_name_base = new_name_base[:-5]

                old_file_path = os.path.join(folder_path, f"{old_name_base}.jpg")
                new_file_path = os.path.join(folder_path, f"{new_name_base}.jpg")

                # check if the original .jpg file exists and rename it
                if os.path.isfile(old_file_path):
                    os.rename(old_file_path, new_file_path)
                    print(f"Renamed {old_name_base}.jpg to {new_name_base}.jpg")
                else:
                    print(f"File not found: {old_name_base}.jpg")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    txt_file_path = '/Users/aleksandra/Desktop/filename_mapping.txt'  
    folder_path = '/Users/aleksandra/Desktop/images2'  
    rename_files_from_txt(txt_file_path, folder_path)


