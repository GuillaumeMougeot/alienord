import yaml
import os
import pandas as pd
import json
from google.cloud.storage import Client
import psutil
import numpy as np
import shutil

class Write_Checked_Images_to_CSV:
    def __init__(self, CONFIG) -> None:
        self.output_directory = CONFIG['output_dir']
        self.checked_img_directories = CONFIG['checked_img_dir_names']
        self.data_directory = CONFIG['data_dir']
        self.meta_directory = CONFIG['meta_dir']  # Path to the folder containing metadata files

    def write_names(self, append_to_existing: bool, nr_images_gcs: int) -> None:
        if not os.path.exists(self.meta_directory):
            print(f"Meta directory '{self.meta_directory}' does not exist. Please check the configuration.")
            return  # Exiting early as the meta directory is critical for operation

        img_dict = {}
        process = psutil.Process()

        for directory in self.checked_img_directories:
            for img_name in os.listdir(os.path.join(self.data_directory, directory)):
                if img_name == '.DS_Store':
                    continue

                meta_file_path = os.path.join(self.meta_directory, f"{os.path.splitext(img_name)[0]}.json")
                try:
                    with open(meta_file_path, 'r') as f:
                        metadata = json.load(f)
                    highest_confidence = max(obj['confidence'] for obj in metadata['objects']) if metadata['objects'] else 0
                except FileNotFoundError:
                    print(f"Metadata file not found for image: {img_name}. Expected at: {meta_file_path}")
                    highest_confidence = 0  # In case the metadata file does not exist

                animal = directory == 'images-anim'
                unblurred_license_plate = directory == 'images-unblurred-license'
                
                if img_name not in img_dict:
                    img_dict[img_name] = [animal, unblurred_license_plate, highest_confidence]
                else:
                    # Update animal, unblurred_license_plate information and confidence
                    if animal:
                        img_dict[img_name][0] = animal
                    if unblurred_license_plate:
                        img_dict[img_name][1] = unblurred_license_plate
                    img_dict[img_name][2] = max(img_dict[img_name][2], highest_confidence)

            print('RAM Used (MB):', process.memory_info().rss / 1000000)

        if not img_dict:  # Check if img_dict is empty
            print("No new images found. No CSV file will be created or updated.")
            return  # Exit the method early


        d = {
            'file_name': list(img_dict.keys()),
            'animal': np.array(list(img_dict.values()))[:, 0].astype(bool), 
            'unblurred_license_plate': np.array(list(img_dict.values()))[:, 1].astype(bool), 
            'confidence': np.array(list(img_dict.values()))[:, 2]
        }
        new_df = pd.DataFrame(d)

        self.sanity_check(new_df, nr_images_in_gcs=nr_images_gcs)

        if append_to_existing:
            try:
                df_old = pd.read_csv(os.path.join(self.output_directory, 'report_roadkill.csv'), index_col=0)
                last_index = df_old.index.max() + 1 if not df_old.empty else 0
            except FileNotFoundError:
                last_index = 0
                df_old = pd.DataFrame(columns=['file_name', 'animal', 'unblurred_license_plate', 'confidence'])
            new_df.index = range(last_index, last_index + len(new_df))
            df = pd.concat([df_old, new_df], ignore_index=False)
        else:
            df = new_df.copy()
            df.index = range(len(df))

        df.to_csv(os.path.join(self.output_directory, 'report_roadkill.csv'), index_label='index')

        print('RAM Used (MB):', process.memory_info().rss / 1000000)

    def read_csv_from_gcs(self, client: Client, bucket_name: str) -> bool:
        bucket = client.get_bucket(bucket_name)
        
        blob = bucket.get_blob('report_roadkill.csv')
        nr_of_images = sum(1 for _ in bucket.list_blobs(prefix= 'images/'))

        if blob is None:
            while True: 
                upload_new_file = input(f'Failed to read "report_roadkill.csv" from {bucket_name}. Upload new file? y/n: ')
                if upload_new_file == 'y':
                    return False, nr_of_images
                elif upload_new_file == 'n':
                    raise FileNotFoundError('Failed to read csv from cloud storage.')
                else:
                    print('Unknown command: Try "y" or "n"')
        
        else:
            blob.download_to_filename(os.path.join(self.output_directory, 'report_roadkill.csv'))
            print(f'Succesfully saved report_roadkill.csv to {self.output_directory}')
            return True, nr_of_images

    def write_to_gcs(self, client: Client, bucket_name: str) -> None:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob('report_roadkill.csv')
        fpath = os.path.join(self.output_directory, 'report_roadkill.csv')

        inp = input(f'Are you sure you want to upload {fpath}? y/n: ')
        if inp == 'y':
            try:
                blob.upload_from_filename(fpath)
                print('File uploaded successfully!')
                self.ask_delete_images()
            except Exception as e:
                print(f'Failed to upload file to GCS. Error: {e}')
        elif inp == 'n':
            print('Uploading cancelled.')

    def ask_delete_images(self):
        folders_to_clear = ['meta', 'checked', 'images-anim', 'images-unblurred-license']
        delete_confirmation = input("Delete images from specified folders? y/n: ")

        if delete_confirmation.lower() == 'y':
            for folder in folders_to_clear:
                self.delete_images_from_folder(folder)
            print("Specified folders cleared.")
        else:
            print("Folder clearing cancelled.")

    def delete_images_from_folder(self, folder_name):
        folder_path = os.path.join(self.data_directory, folder_name)
        try:
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print(f"Contents of '{folder_name}' deleted.")
        except Exception as e:
            print(f"Failed to delete contents of '{folder_name}'. Error: {e}")

    def sanity_check(self, df, nr_images_in_gcs):
        print("Sanity Check:")
        animal_images_count = len([img_name for img_name in os.listdir(os.path.join(self.data_directory, 'images-anim')) if img_name != '.DS_Store'])
        checked_images_count = len([img_name for img_name in os.listdir(os.path.join(self.data_directory, 'checked')) if img_name != '.DS_Store'])
        
        print(f"True labels for animals in dataframe: {sum(df['animal'])}")
        print(f"Images in 'images-anim' folder: {animal_images_count}")
        print(f"Dataframe length: {len(df)}")
        print(f"Images in 'checked' folder: {checked_images_count}")
        print(f"Images in 'data-biodiversity/images/' on GCS: {nr_images_in_gcs}")
        #print(f"True labels for animals in dataframe: {sum(df['animal'])}")


if __name__ == "__main__":
    with open('../data_handling/config.yaml') as file:
        CONFIG = yaml.load(file, Loader=yaml.FullLoader)

    writer = Write_Checked_Images_to_CSV(CONFIG=CONFIG)
    BASE_DIR = os.path.dirname(__file__)
    try:
        client = Client.from_service_account_json(os.path.join(BASE_DIR, CONFIG['gcs_key_filename']))
    except Exception as e:
        print(f"Error initializing storage client: {e}")
        raise NotImplementedError
    bucket_name = "data-biodiversity"

    append_to_existing, nr_images_gcs = writer.read_csv_from_gcs(client, bucket_name)
    writer.write_names(append_to_existing, nr_images_gcs)
    writer.write_to_gcs(client, bucket_name)

    print('Process completed.')
