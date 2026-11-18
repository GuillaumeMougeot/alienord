from dataclasses import dataclass, asdict

@dataclass
class Latitude:
    degrees: int
    minutes: float
    orientation: str

    @staticmethod
    def from_dict(d: dict) -> 'Latitude':
        return Latitude(degrees = d['degrees'],
                        minutes = d['minutes'],
                        orientation = d['orientation'])

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Longitude:
    degrees: int
    minutes: float
    orientation: str

    @staticmethod
    def from_dict(d: dict) -> 'Longitude':
        return Latitude(degrees = d['degrees'],
                        minutes = d['minutes'],
                        orientation = d['orientation'])

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GpsInfo:
    speed_kmh: float
    course: float
    timestamp: str
    latitude: Latitude
    longitude: Longitude

    @staticmethod
    def from_dict(d: dict) -> 'GpsInfo':
        return GpsInfo(
            speed_kmh = d['speed_kmh'],
            course = d['course'],
            timestamp = d['timestamp'],
            latitude = Latitude.from_dict(d['latitude']),
            longitude = Longitude.from_dict(d['longitude'])
        )
    
    def to_dict(self) -> dict:
        return {
            'speed_kmh': self.speed_kmh,
            'course': self.course,
            'timestamp':self.timestamp,
            'latitude': self.latitude.to_dict(),
            'longitude': self.longitude.to_dict(),
        }
    
    def format_geo(self) -> str:
        lat = self.latitude.degrees + self.latitude.minutes / 60
        long = self.longitude.degrees + self.longitude.minutes / 60
        return f"{lat:.5f}{self.latitude.orientation}_{long:.5f}{self.longitude.orientation}"
    