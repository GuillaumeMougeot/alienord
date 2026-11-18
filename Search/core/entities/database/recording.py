from dataclasses import dataclass

from core.entities.database.database_info import DatabaseInfo
from core.entities.annotation_type import AnnotationType
from core.entities.gps import Gps

from utils.utils import date_to_str

@dataclass
class Recording(DatabaseInfo):
    
    @staticmethod
    def from_dict(d: dict) -> 'Recording':
        return Recording(annotation_type = AnnotationType(d['annotation_type']), 
                         image_gs_url = d['image_gs_url'],
                         country = d['country'],
                         device = d['device'],
                         camera_index = d['camera_index'],
                         picture_timestamp = date_to_str(d['picture_timestamp']),
                         uploaded_timestamp = date_to_str(d['uploaded_timestamp']),
                         gps = Gps.from_dict(d['gps']))