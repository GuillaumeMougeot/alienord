from enum import Enum

class Key(str, Enum):
    TIMESTAMP = "picture_timestamp"
    COUNTRY = "country"
    DEVICE = "device"
    PLANT_TYPE = "plant_type"