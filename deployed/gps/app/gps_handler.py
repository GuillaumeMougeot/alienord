import json
from time import time
from typing import Union
from datetime import datetime, timezone, timedelta
from micropyGPS import MicropyGPS
from app.read import ReadLine
from app.configuration import Config
from app.gps import Gps, Latitude, Longitude
from utils.logging import GpsLogger

class GpsHandler:

    def __init__(self, config: Config, logger: GpsLogger):
        self.config = config
        self.logger = logger
        self.datetime_format = "%Y%m%dT%H%M%S.%f"

    def save_gps_with_timestamp(self, gps: MicropyGPS):
        # Drop last three digits since '%f' provides the microseconds
        custom_lastfix_timestamp = datetime.utcnow().strftime(self.datetime_format)[:-3]
        self.logger.info( f'Saving new GPS coordinates. Last fix: {custom_lastfix_timestamp}.')
        gps_info = Gps(speed_kmh = gps.speed[2],
                       course = gps.course,
                       timestamp = custom_lastfix_timestamp,
                       latitude = Latitude(degrees = gps.latitude[0],
                                           minutes = gps.latitude[1],
                                           orientation = gps.latitude[2]),
                       longitude = Longitude(degrees = gps.longitude[0],
                                             minutes = gps.longitude[1],
                                             orientation = gps.longitude[2]))

        with open(self.config.gps.GPS_DATA_PATH, 'w') as f:
            json.dump(gps_info.to_dict(), f, indent=2)
    

    def get_gps_line(self, reader: ReadLine) -> Union[str, None] :
        try:
            return reader.readline().decode()
        except Exception as e:
            self.logger.error(f"""********************
                                Couldn't decode. Reinitiating
                                {e}
                                ********************""")
            return None

    def save_heartbeat(self) -> None:
        with open(self.config.heartbeat.SINK, 'w') as f:
            f.write(str(round(time() * 1000)))

