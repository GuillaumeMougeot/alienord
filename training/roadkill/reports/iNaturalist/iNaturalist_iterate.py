import csv
import subprocess
import os
import shutil
from tqdm import tqdm

def download_photo(id, output_folder):
    temp_dir = os.path.join(output_folder, "temp", id) 
    os.makedirs(temp_dir, exist_ok=True)  

    try:
        command = f'aws s3 cp --no-sign-request s3://inaturalist-open-data/photos/{id}/ {temp_dir} --recursive --exclude "*" --include "*medium*"'
        subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE)
        print('A photo downloaded')


        for filename in os.listdir(temp_dir):
            old_path = os.path.join(temp_dir, filename)
            new_filename = f"{id}_{filename}"
            new_path = os.path.join(output_folder, new_filename)
            shutil.move(old_path, new_path)  # Move and rename the file

        # remove the now empty temporary directory
        os.rmdir(temp_dir)

    except subprocess.CalledProcessError:
        print(f"No files found for ID {id}, or an error occurred.")


output_folder = '/Users/aleksandra/Desktop/Operations/iNaturalist_photos'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


#download CSV file from the website
csv_file_path = '/Users/aleksandra/Desktop/Operations/observations-400243.csv'
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in tqdm(reader):
        inat_id = row['id'].strip()
        url = row["image_url"]
        id = url.split('/photos/')[1].split('/')[0]
        # Check if the ID is not empty before attempting to download
        if id:
            download_photo(id, output_folder)
