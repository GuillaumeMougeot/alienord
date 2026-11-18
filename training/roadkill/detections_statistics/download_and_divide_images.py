import os
from google.cloud import storage
from google.cloud.storage import Client
import pandas as pd 
import json

# Function to load paths from config file
def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

# Load paths from the config file
config = load_config('detections_statistics/config.yml')
file_path = config['animal_confidence_file']
gcs_key_filename = config['gcs_key_filename']
bucket_name = config['data-vd']

client = storage.Client.from_service_account_json(gcs_key_filename)
bucket = client.get_bucket(bucket_name)

# download files from Google Cloud
def download_images(filenames, folder):

    if not os.path.exists(folder):
        os.makedirs(folder)

    for filename in filenames:
        try:
            # Include the 'images/' subdirectory in the blob reference
            blob = bucket.blob(f"images/{filename}")
            if not blob.exists():
                print(f"File images/{filename} does not exist in bucket {bucket.name}.")
                continue
            
            destination_file_name = os.path.join(folder, filename)
            blob.download_to_filename(destination_file_name)
            print(f"Downloaded images/{filename} to {folder}/.")
        except Exception as e:
            print(f"Failed to download images/{filename}. Error: {e}")



def filter_and_download(input_file):
    #low_confidence_animal_true_data = []
    #high_confidence_animal_false_data = []
    high_confidence_animal_true_data = []
    low_confidence_animal_false_data = []
    
    # Read the file and process line by line
    with open(input_file, 'r') as file:
        for line_number, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split(', ')
                filename = parts[0].split(': ')[1]
                confidence = float(parts[2].split(': ')[1])
                animal = parts[3].split(': ')[1].strip()

                # Append to respective list as dictionaries
                # confidence of true-positives
                if confidence >= 0.5 and animal == 'True':
                    high_confidence_animal_true_data.append({
                        'Filename': filename,
                        'Confidence': confidence,
                        'Animal': animal
                    })
                
                # confidence of false-positives 
                elif confidence < 0.5 and animal == 'False':
                    low_confidence_animal_false_data.append({
                        'Filename': filename,
                        'Confidence': confidence,
                        'Animal': animal
                    })
            except IndexError:
                print(f"Error processing line {line_number}: '{line}'. Line is not in the expected format.")
            except ValueError as e:
                print(f"Error processing line {line_number}: '{line}'. {e}")

    # Convert lists of dictionaries to pandas DataFrames for display
    if high_confidence_animal_true_data:
        low_confidence_df = pd.DataFrame(high_confidence_animal_true_data)
        print("Low Confidence, Animal True Table:")
        print(low_confidence_df)
        # Extract filenames and call download_images
        low_conf_filenames = [f"{row['Filename'].replace('.json', '.jpg')}" for row in high_confidence_animal_true_data]
        download_images(low_conf_filenames, 'high_confidence_animal_true')
    else:
        print("No entries found for Low Confidence, Animal True.")

    if low_confidence_animal_false_data:
        high_confidence_df = pd.DataFrame(low_confidence_animal_false_data)
        print("High Confidence, Animal False Table:")
        print(high_confidence_df)
        high_conf_filenames = [f"{row['Filename'].replace('.json', '.jpg')}" for row in low_confidence_animal_false_data]
        download_images(high_conf_filenames, 'low_confidence_animal_false')
    else:
        print("No entries found for High Confidence, Animal False.")

# run the function with the input text file
filter_and_download(file_path)
