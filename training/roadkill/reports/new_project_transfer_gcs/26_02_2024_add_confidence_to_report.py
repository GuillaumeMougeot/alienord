
import pandas as pd
import os
import json

csv_file_path = '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/reports/report_roadkill.csv'
input_folder_path = '/Users/aleksandra/Desktop/biodiversity/'
output_csv_file_path = '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/reports/report_roadkill_new.csv'

df = pd.read_csv(csv_file_path)
df['confidence'] = 0.0

# function to find and open a JSON file, then return the highest confidence value
def get_highest_confidence(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        confidences = [obj['confidence'] for obj in data['objects']]
        print(f"Confidence values in {os.path.basename(json_file_path)}: {confidences}")
        return max(confidences) if confidences else 0

# iterate over each row in the DataFrame
for index, row in df.iterrows():
    json_file_name = row['file_name'].strip().replace('.jpg', '.json')
    print(f"Looking for JSON file: {json_file_name}")
    
    found_json = False
    for subdir, dirs, files in os.walk(input_folder_path):
        print(f"Checking in: {subdir}")  # Debugging: Which directory are we checking?
        if json_file_name in files:
            found_json = True
            json_file_path = os.path.join(subdir, json_file_name)
            print(f"Found compatible JSON file for {row['file_name']}: {json_file_path}")
            df.at[index, 'confidence'] = get_highest_confidence(json_file_path)
            break

    if not found_json:
        print(f"No compatible JSON file found for {row['file_name']}.")

# save the updated DataFrame to a new CSV file, including the column names
df.to_csv(output_csv_file_path, index=False)

print(f"Updated DataFrame saved to {output_csv_file_path}")