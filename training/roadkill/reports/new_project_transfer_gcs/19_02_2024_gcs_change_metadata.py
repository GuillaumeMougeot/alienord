import os
import json
from datetime import datetime

metadata_path = "/Users/aleksandra/Desktop/meta"
new_metadata_file = "/Users/aleksandra/Desktop/new_meta"
filename_mapping_file = "/Users/aleksandra/Desktop/filename_mapping.txt"  

def format_gps_timestamp(gps_timestamp):
    dt = datetime.strptime(gps_timestamp, "%Y-%m-%d %H:%M:%S%z")
    return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]

def format_app_timestamp(app_timestamp):
    dt = datetime.utcfromtimestamp(app_timestamp / 1000.0)
    return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]

def format_coordinates(lat, lon):
    # latitude
    lat_deg = abs(lat[0]) + lat[1] / 60
    lat_dir = lat[2]
    lat_str = f"{lat_deg:.5f}{lat_dir}"
    # longitude
    lon_deg = abs(lon[0]) + lon[1] / 60
    lon_dir = lon[2]
    lon_str = f"{lon_deg:.5f}{lon_dir}"
    return lat_str, lon_str



def save_new_metadata(new_metadata, new_filename):
    new_file_path = os.path.join(new_metadata_file, new_filename + '.json')
    with open(new_file_path, 'w') as outfile:
        json.dump(new_metadata, outfile, indent=4)
    print(f"Saved new metadata to {new_file_path}")



def create_new_metadata():
    if not os.path.exists(new_metadata_file):
        os.makedirs(new_metadata_file)
        
    with open(filename_mapping_file, 'w') as mapping_file:
        for filename in os.listdir(metadata_path):
            try:
                file_path = os.path.join(metadata_path, filename)
                with open(file_path, 'r') as file:
                    data = json.load(file)

                country = "Denmark" if data["device_id"] == "xnx1" else "Sweden"
                lat_str, lon_str = format_coordinates(data["gps"]["latitude"], data["gps"]["longitude"])
       
                new_metadata = {
                    "country": country,
                    "device": data["device_id"],
                    "camera_index": data["pad_index"],
                    "picture_timestamp": format_app_timestamp(data["app_timestamp"]),
                    "gps": {
                        "speed_kmh": data["gps"]["speed_kmh"],
                        "course": data["gps"]["course"],
                        "timestamp": format_gps_timestamp(data["gps"]["gps_timestamp"]),
                        "latitude": {
                            "degrees": data["gps"]["latitude"][0],
                            "minutes": data["gps"]["latitude"][1],
                            "orientation": data["gps"]["latitude"][2],
                        },
                        "longitude": {
                            "degrees": data["gps"]["longitude"][0],
                            "minutes": data["gps"]["longitude"][1],
                            "orientation": data["gps"]["longitude"][2],
                        },
                    },
                    "objects": [{
                        "class_label": obj["class_label"],
                        "display_label": obj["class_label"].replace('_', ' ').title(),
                        "confidence": float(obj["confidence"]),
                        "model": "20230830150000_yolov8m_10classes_roadkill",
                        "bbox_normalized": obj["rect_params_normalized"]
                    } for obj in data["objects"]]
                }

            # GPS coordinates
            
                picture_timestamp = format_app_timestamp(data["app_timestamp"])
                gps_timestamp = format_gps_timestamp(data["gps"]["gps_timestamp"])
                new_filename = f"{data['device_id']}_{picture_timestamp}_{lat_str}_{lon_str}_c{str(data['pad_index']).zfill(2)}"

                # save the new metadata
                save_new_metadata(new_metadata, new_filename)
                
                # write the original and new filenames to the mapping file
                mapping_file.write(f"{filename}, {new_filename}.json\n")
            except Exception as e:
                print(f"Could not process file {filename}. Error: {e}")

create_new_metadata()