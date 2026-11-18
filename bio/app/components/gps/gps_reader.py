import json
from datetime import datetime, timedelta
from schemas.generated.config import Gps
from utils.logging import BioLogger
from app.components.gps import GpsInfo

class GpsReader:

    @staticmethod
    def load_gps_info(path: str) -> GpsInfo:
        with open(path, 'r') as f:
            data = json.load(f)
        return GpsInfo.from_dict(data)
    
    @staticmethod
    def check_running_timestamp(gps_info: GpsInfo, drift_seconds: int = 300) -> bool:
        """
        Check that the gps updates script is running by checking the last timestamp.

        This allows for a time drift of `drift_seconds`, meaning it will consider timestamps 
        to be "recent enough" if they fall in the window between `NOW` and `drift_seconds` ago.
        """
        last_dt = datetime.strptime(gps_info.timestamp, "%Y%m%dT%H%M%S.%f")
        return datetime.utcnow() - last_dt <= timedelta(seconds=drift_seconds) 

