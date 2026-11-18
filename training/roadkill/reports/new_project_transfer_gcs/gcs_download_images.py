import os
import pandas as pd
from google.cloud.storage import Client
import json

def read_filenames_from_txt(file_path: str, delimiter=',') -> list:
    # check if the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    # initialize a list to store filenames
    filenames = []

    # read the file line by line and extract the filenames
    try:
        with open(file_path, 'r') as file:
            for line in file:
                filename = line.split(delimiter)[0].strip()
                if filename.endswith('.json'):
                    filename = filename[:-5] + '.jpg'
                filenames.append(filename)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return filenames

def download_unchecked_images(filenames: list, data_dir: str, client: Client, bucket_name: str) -> None:
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    blob_path = 'images/'
    bucket = client.get_bucket(bucket_name)

    for blob in bucket.list_blobs(prefix=blob_path):
        blob_name = os.path.basename(blob.name)
        if blob_name in filenames:
            print(f'Downloading {blob_name}...')
            blob.download_to_filename(os.path.join(data_dir, blob_name))

    return



if __name__ == "__main__":
    txt_file_path = '/Users/aleksandra/Desktop/filename_mapping.txt'
    delimiter = ','
    # GCS stuff
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG = {
        'gcs_key_filename': '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/secrets/gcs_key.json',
        'data_dir': '/Users/aleksandra/Desktop/images'  
    }

    try:
        client = Client.from_service_account_json(os.path.join(BASE_DIR, CONFIG['gcs_key_filename']))
    except Exception as e:
        print(f"Couldn't init storage client: {e}")
        raise NotImplementedError

    bucket_name = "data-vd"
    filenames = read_filenames_from_txt(txt_file_path, delimiter)
    print(filenames)
    download_unchecked_images(filenames, CONFIG['data_dir'], client, bucket_name)
    
    print('Process finished successfully!')
