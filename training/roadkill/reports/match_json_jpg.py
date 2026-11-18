import os
import shutil

def match_json_jpg_files(json_folder, jpg_folder, output_folder):

    # retrieve all .json files from the directory
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    
    # for each .json file, check if there's a matching .jpg file
    for json_file in json_files:
        
        # create the jpg filename (by changing the extension from .json to .jpg)
        jpg_file = json_file.replace('.json', '.jpg')
        
        # path to the jpg file in the jpg folder
        jpg_file_path = os.path.join(jpg_folder, jpg_file)
        
        # if the jpg file exists, copy it to the output directory
        if os.path.exists(jpg_file_path):
            shutil.copy(jpg_file_path, output_folder)
            print(f'File {jpg_file} copied to directory {output_folder}')

if __name__ == '__main__':
    json_folder_path = 'path to the metadata'
    jpg_folder_path = 'path to images'
    output_folder_path = 'path to the output folder'
    
    match_json_jpg_files(json_folder_path, jpg_folder_path, output_folder_path)