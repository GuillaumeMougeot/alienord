from dataclasses import dataclass
from typing import List

from app.components.gps import GpsInfo
from app.configuration import config

from core.domain.geom import BBox
from core.domain.detection import Obj

@dataclass
class ObjectDetection:

    version: str
    class_label: str
    display_label: str
    confidence: float
    model: str
    bbox_normalized: BBox

    def to_dict(self):
        return {
            'version': self.version,
            'class_label': self.class_label,
            'display_label': self.display_label,
            'confidence': self.confidence,
            'model': self.model,
            'bbox_normalized':{
                'left': self.bbox_normalized.left,
                'top': self.bbox_normalized.top,
                'width': self.bbox_normalized.width,
                'height': self.bbox_normalized.height
            }
        }

@dataclass
class CarDetection(ObjectDetection):
    pass

@dataclass
class AnimalDetection(ObjectDetection):
    pass

@dataclass
class PlantDetection(ObjectDetection):
    plant_type: str

    def to_dict(self):
        return {
            'version': self.version,
            'class_label': self.class_label,
            'plant_type': self.plant_type,
            'display_label': self.display_label,
            'confidence': self.confidence,
            'model': self.model,
            'bbox_normalized':{
                'left': self.bbox_normalized.left,
                'top': self.bbox_normalized.top,
                'width': self.bbox_normalized.width,
                'height': self.bbox_normalized.height
            }
        }

@dataclass
class FrameDetection:
    country: str
    device: str
    camera_index: int
    timestamp: str
    gps: GpsInfo
    objects: List[ObjectDetection]

    def to_dict(self) -> dict:
        return {
            'country': self.country,
            'device': self.device,
            'camera_index': self.camera_index,
            'timestamp': self.timestamp,
            'gps': self.gps.to_dict(),
            'objects': [obj.to_dict() for obj in self.objects]
        }