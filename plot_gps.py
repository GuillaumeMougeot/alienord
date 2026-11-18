import argparse
import subprocess
import re
import folium
import csv
from collections import defaultdict
from typing import List, Tuple
from folium.plugins import MarkerCluster, HeatMap

def list_gcs_bucket(bucket_name: str) -> List[str]:
    """
    List the contents of a Google Cloud Storage bucket and capture the output.

    Parameters:
        bucket_name (str): The name of the GCS bucket.

    Returns:
        List[str]: The output from the `gsutil ls` command.
    """
    result = subprocess.run(["gsutil", "ls", f"gs://{bucket_name}"], capture_output=True, text=True)
    result.check_returncode()
    return result.stdout.splitlines()

def parse_coordinates(names: List[str]) -> List[Tuple[str, float, float, str]]:
    """
    Extract and convert GPS coordinates and dates from filenames.

    Parameters:
        names (list of str): List of filenames.

    Returns:
        list of tuple: A list of tuples containing date, latitude, longitude, and filename.
    """
    regex = r"(\d{8})T(\d{6}\.\d+)_([\d\.]+)([NS])_([\d\.]+)([EW])"
    gps_and_dates = []

    for name in names:
        if "no_gps" in name:
            continue
        
        match = re.search(regex, name)
        if match:
            date_str, _, lat, lat_dir, lon, lon_dir = match.groups()
            date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            lat = float(lat) * (1 if lat_dir == "N" else -1)
            lon = float(lon) * (1 if lon_dir == "E" else -1)
            gps_and_dates.append((date, lat, lon, name))
    
    return gps_and_dates

def get_bounds(gps_coords: List[Tuple[str, float, float, str]]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box with a 0.2-degree margin.

    Parameters:
        gps_coords (list of tuple): List of tuples containing date, latitude, longitude, and filename.

    Returns:
        tuple: A tuple containing minimum latitude, maximum latitude, minimum longitude, and maximum longitude.
    """
    if not gps_coords:
        return 0, 0, 0, 0

    latitudes, longitudes = zip(*[(lat, lon) for _, lat, lon, _ in gps_coords])
    
    min_lat = min(latitudes) - 0.2
    max_lat = max(latitudes) + 0.2
    min_lon = min(longitudes) - 0.2
    max_lon = max(longitudes) + 0.2
    
    return min_lat, max_lat, min_lon, max_lon

def create_csv(filenames: List[str], csv_output: str) -> None:
    """
    Create a CSV with filenames and other info (date, hour, lat, lon).
    Count duplicates, add it to the NumImages column, and save the filename
    of at least one example of every unique entry.

    Parameters:
        filenames (list of str): List of filenames.
        csv_output (str): Output CSV file name.
    """
    entries = defaultdict(lambda: {"count": 0, "filename": ""})
    
    for name in filenames:
        match = re.search(r"(\d{8})T(\d{6}\.\d+)_([\d\.]+)([NS])_([\d\.]+)([EW])", name)
        if match:
            date_str, time_str, lat_str, lat_dir, lon_str, lon_dir = match.groups()
            date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            lat = float(lat_str) * (1 if lat_dir == "N" else -1)
            lon = float(lon_str) * (1 if lon_dir == "E" else -1)
            
            entry = (date, time, lat, lon)
            entries[entry]["count"] += 1
            if entries[entry]["count"] == 1:
                name = name.replace('gs://', 'https://storage.cloud.google.com/')
                entries[entry]["filename"] = name
    
    with open(csv_output, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Hour", "Latitude", "Longitude", "NumImages", "ExampleFilename"])
        for entry, details in entries.items():
            writer.writerow([*entry, details["count"], details["filename"]])

def create_map(gps_coords: List[Tuple[str, float, float, str]], map_output: str) -> None:
    """
    Create and save a map with markers, overall heatmap, and date-based heatmaps grouped into one layer.

    Parameters:
        gps_coords (list of tuple): List of tuples containing date, latitude, longitude, and filename.
        map_output (str): Output HTML map file name.
    """
    # Color map for different dates
    colors = [
        "blue", "green", "red", "purple", "orange", "darkblue", "lightred", 
        "beige", "darkgreen", "darkpurple", "cadetblue", "lightblue", "lightgreen"
    ]
    
    date_color_map = {}
    unique_dates = sorted(set(date for date, _, _, _ in gps_coords))
    for i, date in enumerate(unique_dates):
        date_color_map[date] = colors[i % len(colors)]
    
    min_lat, max_lat, min_lon, max_lon = get_bounds(gps_coords)
    map_center = [(max_lat + min_lat) / 2, (max_lon + min_lon) / 2]
    map_ = folium.Map(location=map_center, zoom_start=10)
    
    # Marker layer
    marker_cluster = MarkerCluster(name='Markers').add_to(map_)
    
    # Heatmap layer for all data
    overall_heat_data = []
    # Heatmap layer based on dates
    heat_data_by_date = defaultdict(list)
    
    for date, lat, lon, filename in gps_coords:
        # Add marker to marker cluster
        color = date_color_map[date]
        file_url = filename.replace('gs://', 'https://storage.cloud.google.com/')
        popup_text = f"Date: {date}<br><a href='{file_url}' target='_blank'>Image</a>"
        folium.Marker(location=[lat, lon],
                      icon=folium.Icon(color=color, icon="info-sign"),
                      popup=popup_text).add_to(marker_cluster)
        
        # Add data to overall heatmap
        overall_heat_data.append([lat, lon])
        
        # Add data to date-based heatmap layers
        heat_data_by_date[date].append([lat, lon])
    
    # Add overall heatmap layer
    HeatMap(overall_heat_data, name='Overall Heatmap', show=False).add_to(map_)
    
    # Add date-based heatmap layers to a feature group
    date_group = folium.FeatureGroup(name='Date-Based Heatmaps').add_to(map_)
    
    for date, heat_data in heat_data_by_date.items():
        color = date_color_map[date]
        HeatMap(heat_data,
                name=f'Heatmap for {date}',
                min_opacity=0.2,
                gradient={0.2: color, 0.6: color, 1: 'white'}).add_to(date_group)
    
    # Add layer control
    folium.LayerControl().add_to(map_)
    
    map_.save(map_output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Google Cloud Storage bucket content and generate CSV and map.")
    parser.add_argument("bucket_name", type=str, help="The name of the GCS bucket.")
    parser.add_argument("--csv_output", type=str, default="recordings.csv", help="Output CSV file name.")
    parser.add_argument("--map_output", type=str, default="map.html", help="Output HTML map file name.")
    args = parser.parse_args()

    names = list_gcs_bucket(args.bucket_name)
    gps_coords = list(set(parse_coordinates(names)))  # Remove duplicates
    
    create_csv(names, args.csv_output)
    create_map(gps_coords, args.map_output)
