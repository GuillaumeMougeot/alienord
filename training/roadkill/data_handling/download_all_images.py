import yaml
import os
import pandas as pd
from google.cloud.storage import Client
#import psutil # only used to keep track of memory usage
from io import BytesIO, StringIO
from google.cloud import storage

def read_csv_from_gcs(client: Client, bucket_name: str) -> None:
    '''
    Get load the checked_imgs.csv file inside gcs to identify the images with animals
    '''
    bucket = client.get_bucket(bucket_name)
    
    blob = bucket.get_blob('checked_imgs.csv')

    # If loading of blob goes wrong:
    if blob is None:
        raise FileNotFoundError('read_csv_gcs() failed to read csv from cloud storage.')
    
    # Load csv as a pandas dataframe
    else:
        
        csv_data = blob.download_as_text()
        dataframe = pd.read_csv(StringIO(csv_data))
        # print(sys.getsizeof(dataframe)/1000000) # Print memory usage in MB

        return dataframe

#improve for me this function to check if in df line we have both conditions accepted: in colunm "animal" =True/False and os.path.basename(blob.name) = dataframe['image_name']

def download_checked_images(dataframe: pd.DataFrame, data_dir:str, client: storage.Client, bucket_name:str) -> None:
    non_animals_output_path = os.path.join(data_dir, 'all_checked_images')
    animals_output_path = os.path.join(data_dir, 'all_animal_images')

    if not os.path.exists(non_animals_output_path):
        os.makedirs(non_animals_output_path)
    if not os.path.exists(animals_output_path):
        os.makedirs(animals_output_path)

    blob_path = 'images/'
    bucket = client.get_bucket(bucket_name)

    # Create a dictionary of image_name to animal status for quick lookup
    image_name_to_animal_status = dict(zip(dataframe['image_name'], dataframe['animal']))

    for blob in bucket.list_blobs(prefix=blob_path):
        image_name = os.path.basename(blob.name)
        if image_name in image_name_to_animal_status:
            if image_name_to_animal_status[image_name]: 
                download_path = animals_output_path
            else:  # False for non-animal
                download_path = non_animals_output_path
            blob.download_to_filename(os.path.join(download_path, image_name))
    return



if __name__ == "__main__":
    
    with open("./data_handling/config.yaml") as file:
        CONFIG = yaml.load(file, Loader=yaml.FullLoader)
    
    # gcs stuff
    BASE_DIR = os.path.dirname(__file__)
    try:
        client = Client.from_service_account_json(os.path.join(BASE_DIR, CONFIG['gcs_key_filename']))
    except Exception as e:
        print(f"Couldn't init storage client: {e}") # TODO: This can be done a bit more smoothly lol
        raise NotImplementedError
    
    bucket_name = "data-vd"
    
    df = read_csv_from_gcs(client, bucket_name)

    download_checked_images(df, CONFIG['data_dir'], client, bucket_name)
    
    print('Process finished sucesfully!')
    
    