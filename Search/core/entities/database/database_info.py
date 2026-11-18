from dataclasses import dataclass

from core.entities.annotation_type import AnnotationType
from core.entities.gps import Gps

from utils.utils import str_to_date

@dataclass
class DatabaseInfo:
    annotation_type: AnnotationType
    image_gs_url: str = None
    country: str = None
    device: str = None
    camera_index: int = None
    picture_timestamp: str = None
    uploaded_timestamp: str = None
    gps: Gps = None

    def to_dict(self):
        return {
            'annotation_type': self.annotation_type.value,
            'image_gs_url': self.image_gs_url,
            'country': self.country,
            'device': self.device,
            'camera_index': self.camera_index,
            'picture_timestamp': str_to_date(self.picture_timestamp),
            'uploaded_timestamp': str_to_date(self.uploaded_timestamp),
            'gps': self.gps.to_dict()
        }