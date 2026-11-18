import os
import json
import csv
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime



# load paths from config file
def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

config = load_config('detections_statistics/config.yml')
metadata_path = config['metadata_path']
checked_images_csv_path = config['checked_images_csv_path']
animal_confidence_file = config['animal_confidence_file']

table = []

# Define the cutoff date - the date from we want to get results
cutoff_date = datetime.strptime("2023-09-15", "%Y-%m-%d")

for filename in os.listdir(metadata_path):
    file_path = os.path.join(metadata_path, filename)
    
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
            # parse the "gps_timestamp"
            gps_timestamp_str = data["gps"]["gps_timestamp"]
            gps_timestamp = datetime.strptime(gps_timestamp_str.split('+')[0], "%Y-%m-%d %H:%M:%S")
            
            
            # check if the timestamp is after the cutoff date
            if gps_timestamp > cutoff_date:
                for obj in data["objects"]:
                    table_entry = {
                        "filename": filename,
                        "gps_timestamp": gps_timestamp_str,
                        "confidence": obj["confidence"]
                    }
                    table.append(table_entry)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for file: {filename}")
            continue

# remove extensions from files
def remove_extension(filename):
    return os.path.splitext(filename)[0]

# prepare list of files 
image_name_to_animal = {}
with open(checked_images_csv_path, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        image_name_to_animal[remove_extension(row['image_name'])] = row['animal']

# update the table with animal value based on the name of file
for entry in table:
    if remove_extension(entry['filename']) in image_name_to_animal:
        entry['animal'] = image_name_to_animal[remove_extension(entry['filename'])]
    else:
        entry['animal'] = 'N/A'

def filter_highest_confidence(entries):
    # Group by filename
    grouped_by_filename = {}
    for entry in entries:
        if entry['filename'] not in grouped_by_filename:
            grouped_by_filename[entry['filename']] = []
        grouped_by_filename[entry['filename']].append(entry)
    
    # For each filename group, select the entry with the highest confidence
    highest_confidence_entries = []
    for filename, group in grouped_by_filename.items():
        highest_confidence_entry = max(group, key=lambda x: x['confidence'])
        highest_confidence_entries.append(highest_confidence_entry)

    return highest_confidence_entries

# apply the function
table = filter_highest_confidence(table)

# save the table with confidences to a txt file
with open(animal_confidence_file, 'w') as output_file:
    for entry in table:
        output_line = f"Filename: {entry['filename']}, GPS Timestamp: {entry['gps_timestamp']}, Confidence: {entry['confidence']}, Animal: {entry['animal']}\n"
        output_file.write(output_line)

print(f"Table saved to {animal_confidence_file}")

