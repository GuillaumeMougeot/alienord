import os
import pandas as pd
from google.cloud.storage import Client
import json

def read_filenames_from_txt(file_path: str) -> pd.DataFrame:
    # Read the file
    with open(file_path, 'r') as file:
        data = file.read()

    # Convert JSON string to a dictionary
    data_dict = json.loads(data)

    # Extract filenames and convert them to .png
    filenames = [name.split('.')[0] + '.png' for name in data_dict.keys()]

    # Convert list of filenames to a DataFrame
    return pd.DataFrame({'image_name': filenames})

def download_unchecked_images(dataframe: pd.DataFrame, data_dir: str, client: Client, bucket_name: str) -> None:
    # Output local path
    output_path = data_dir
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    blob_path = 'images/'
    bucket = client.get_bucket(bucket_name)

    for blob in bucket.list_blobs(prefix=blob_path):
        if os.path.basename(blob.name) in dataframe['image_name'].values:
            blob.download_to_filename(os.path.join(output_path, os.path.basename(blob.name)))

    return

if __name__ == "__main__":
    # Define the path to your .txt file
    txt_file_path = '/path/to/your/file.txt'

    # GCS stuff
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG = {
        'gcs_key_filename': 'path/to/your/service_account.json',
        'data_dir': '/Users/aleksandra/Desktop/images'  # Update this path as needed
    }

    try:
        client = Client.from_service_account_json(os.path.join(BASE_DIR, CONFIG['gcs_key_filename']))
    except Exception as e:
        print(f"Couldn't init storage client: {e}")
        raise NotImplementedError

    bucket_name = "data-vd"

    # Read filenames from txt file
    df = read_filenames_from_txt(txt_file_path)

    download_unchecked_images(df, CONFIG['data_dir'], client, bucket_name)
    
    print('Process finished successfully!')
