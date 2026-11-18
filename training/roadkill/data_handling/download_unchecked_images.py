import yaml
import os
import pandas as pd
from google.cloud.storage import Client
from io import BytesIO, StringIO

def read_csv_from_gcs(client: Client, bucket_name: str) -> pd.DataFrame:
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob('report_roadkill.csv')
    if blob is None:
        raise FileNotFoundError('read_csv_gcs() failed to read csv from cloud storage.')
    else:
        csv_data = blob.download_as_text()
        dataframe = pd.read_csv(StringIO(csv_data))
        dataframe['file_name'] = dataframe['file_name'].str.replace(' ', '')
        return dataframe

def download_unchecked_images(dataframe: pd.DataFrame, data_dir:str, client: Client, bucket_name:str, subfolders:list) -> None:
    unchecked_path = os.path.join(data_dir, 'unchecked')
    meta_path = os.path.join(data_dir, 'meta')

    if not os.path.exists(unchecked_path):
        os.makedirs(unchecked_path)
        print(f"'unchecked_images' folder created at: {unchecked_path}")
    if not os.path.exists(meta_path):
        os.makedirs(meta_path)
        print(f"'meta' folder created at: {meta_path}")
        
    bucket = client.get_bucket(bucket_name)
    downloaded_images_count = 0  

    for subfolder in subfolders:
        image_blob_path = f'images/{subfolder}/'
        
        for blob in bucket.list_blobs(prefix=image_blob_path):
            if not blob.name.endswith('/') and 'c00' in os.path.basename(blob.name):
                file_name_no_spaces = os.path.basename(blob.name).replace(' ', '')
                if file_name_no_spaces not in dataframe['file_name'].values:
                    # Downloading the image
                    image_target_path = os.path.join(unchecked_path, file_name_no_spaces)
                    blob.download_to_filename(image_target_path)
                    downloaded_images_count += 1
                    
                    meta_file_name = os.path.splitext(file_name_no_spaces)[0] + '.json'
                    meta_target_path = os.path.join(meta_path, meta_file_name)
                    meta_blob_path = f'meta/{subfolder}/' + meta_file_name
                    meta_blob = bucket.get_blob(meta_blob_path)
                    if meta_blob:
                        meta_blob.download_to_filename(meta_target_path)

    print(f"Total number of new images: {downloaded_images_count}")



if __name__ == "__main__":
    
    with open("../data_handling/config.yaml") as file:
        CONFIG = yaml.load(file, Loader=yaml.FullLoader)
    
    BASE_DIR = os.path.dirname(__file__)
    try:
        client = Client.from_service_account_json(os.path.join(BASE_DIR, CONFIG['gcs_key_filename']))
    except Exception as e:
        print(f"Couldn't init storage client: {e}") 
        raise NotImplementedError
    
    bucket_name = "data-biodiversity"
    
    df = read_csv_from_gcs(client, bucket_name)
    subfolders = CONFIG['subfolders']  # Now reading subfolders from the config file
    download_unchecked_images(df, CONFIG['data_dir'], client, bucket_name, subfolders)
    
    print('Downloading finished successfully!')
