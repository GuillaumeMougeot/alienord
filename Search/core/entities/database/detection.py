from typing import List
from dataclasses import dataclass, field

from core.entities.annotation_type import AnnotationType
from core.entities.object import Object
from core.entities.gps import Gps
from core.entities.database.database_info import DatabaseInfo

from utils.utils import str_to_date, date_to_str

@dataclass
class Detection(DatabaseInfo):
    image_public_url: str = None
    objects: List[Object] = field(default_factory=list)
    image_complete: bool = False
    meta_complete: bool = False
    animal: bool = False
    plant: bool = False
    plant_type: List[str] = field(default_factory=list)
    
    @staticmethod
    def from_dict(d: dict) -> 'Detection':
        return Detection(annotation_type = AnnotationType(d['annotation_type']), 
                         image_gs_url = d['image_gs_url'],
                         image_public_url = d['image_public_url'],
                         country = d['country'],
                         device = d['device'],
                         camera_index = d['camera_index'],
                         picture_timestamp = date_to_str(d['picture_timestamp']),
                         uploaded_timestamp = date_to_str(d['uploaded_timestamp']),
                         gps = Gps.from_dict(d['gps']),
                         objects = [Object.from_dict(obj) for obj in d['objects']],
                         animal = d['animal'],
                         plant = d['plant'],
                         plant_type = d['plant_type'],
                         image_complete = d['image_complete'],
                         meta_complete = d['meta_complete'])

    def to_dict(self):
        return {
            'annotation_type': self.annotation_type.value,
            'image_gs_url': self.image_gs_url,
            'image_public_url': self.image_public_url,
            'country': self.country,
            'device': self.device,
            'camera_index': self.camera_index,
            'picture_timestamp': str_to_date(self.picture_timestamp),
            'uploaded_timestamp': str_to_date(self.uploaded_timestamp),
            'animal': self.animal,
            'plant': self.plant,
            'plant_type': self.plant_type,
            'image_complete': self.image_complete,
            'meta_complete': self.meta_complete,
            'gps': self.gps.to_dict() if self.gps else None,
            'objects': [obj.to_dict() for obj in self.objects] if self.objects else []
        }
    
    @staticmethod
    def to_http_response(d: dict) -> dict:
        return {
            'image_gs_url': d['image_gs_url'],
            'image_public_url': d['image_public_url'],
            'country': d['country'],
            'device': d['device'],
            'camera_index': d['camera_index'],
            'picture_timestamp': date_to_str(d['picture_timestamp']),
            'uploaded_timestamp': date_to_str(d['uploaded_timestamp']),
            'gps': d['gps'],
            'objects': d['objects']
        }