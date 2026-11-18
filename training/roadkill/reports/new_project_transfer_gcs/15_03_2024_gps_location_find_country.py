import os
import json
from random import randint
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def degrees_to_decimal(degrees, minutes, orientation):
    decimal = degrees + minutes / 60.0
    if orientation in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_country_from_coordinates(latitude, longitude):
    user_agent = 'user_me_{}'.format(randint(10000,99999))
    geolocator = Nominatim(user_agent=user_agent)
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location:
            address = location.raw['address']
            country = address.get('country', 'Country not found')
            if country == "Deutschland":
                return "Germany"
            if country == "Danmark":
                return "Denmark"
            return country
    except GeocoderTimedOut:
        return "Geocoder timed out"
    return "Country not found"

def main(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)
                gps_data = data['gps']
                latitude = degrees_to_decimal(gps_data['latitude']['degrees'], gps_data['latitude']['minutes'], gps_data['latitude']['orientation'])
                longitude = degrees_to_decimal(gps_data['longitude']['degrees'], gps_data['longitude']['minutes'], gps_data['longitude']['orientation'])
                new_country = get_country_from_coordinates(latitude, longitude)
                # Check if the country has changed
                current_country = data.get('country', None)
                if new_country != current_country:
                    print(f"Country name changed in {filename} from '{current_country}' to '{new_country}'.")
                    data['country'] = new_country
                    # Write the updated dictionary back to the file
                    with open(file_path, 'w') as file:
                        json.dump(data, file, indent=4)
                else:
                    print(f"{filename}: No change in country name ('{current_country}').")

main('/Users/aleksandra/Desktop/xnx2')
