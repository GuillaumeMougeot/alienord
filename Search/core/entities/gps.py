from dataclasses import dataclass
from math import floor

from core.entities.orientation import Orientation

@dataclass
class Coordinate:
    degrees: int
    minutes: float
    orientation: Orientation

    def to_dict(self):
        return {
            'degrees': self.degrees,
            'minutes': self.minutes,
            'orientation': self.orientation.value
        }

@dataclass
class Latitude(Coordinate):
    
    @staticmethod
    def from_dict(d: dict) -> 'Latitude':
        return Latitude(degrees = d['degrees'], 
                        minutes = d['minutes'],
                        orientation = Orientation(d['orientation']))
    @staticmethod
    def geo_to_coordinate(geo: str) -> 'Latitude':
        lat = float(geo[:-1])
        return Latitude(degrees = floor(lat),
                        minutes = (lat%1)*60,
                        orientation = Orientation(geo[-1]))

@dataclass
class Longitude(Coordinate):

    @staticmethod
    def from_dict(d: dict) -> 'Longitude':
        return Longitude(degrees = d['degrees'],
                         minutes = d['minutes'],
                         orientation = Orientation(d['orientation']))
    
    @staticmethod
    def geo_to_coordinate(geo: str) -> 'Longitude':
        lon = float(geo[:-1])
        return Longitude(degrees = floor(lon), 
                         minutes = (lon%1)*60,
                         orientation = Orientation(geo[-1]))

@dataclass
class Gps:
    speed_kmh: float
    course: float
    timestamp: str
    latitude: Latitude
    longitude: Longitude

    @staticmethod
    def from_dict(d: dict):
        return Gps(speed_kmh = d['speed_kmh'],
                   course = d['course'],
                   timestamp = d['timestamp'],
                   latitude = Latitude.from_dict(d['latitude']),
                   longitude = Longitude.from_dict(d['longitude']))

    def to_dict(self):
        return{
            'speed_kmh': self.speed_kmh,
            'course': self.course,
            'timestamp': self.timestamp,
            'latitude': self.latitude.to_dict(),
            'longitude': self.longitude.to_dict()
        }