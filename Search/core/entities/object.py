from dataclasses import dataclass

from core.entities.bbox import BBox

@dataclass
class Object:
    version: str
    class_label: str
    display_label: str
    confidence: float
    model: str
    bbox_normalized: BBox

    @staticmethod
    def from_dict(d: dict) -> 'Object':
        detection_type = d['class_label']
        if 'plant' in detection_type.lower():
            return Plant.from_dict(d)
        elif 'animal' in detection_type.lower():
            return Animal.from_dict(d)

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'class_label': self.class_label,
            'display_label': self.display_label,
            'confidence': self.confidence,
            'model': self.model,
            'bbox_normalized': self.bbox_normalized.to_dict()
        }

@dataclass
class Animal(Object):
    
    @staticmethod
    def from_dict(d: dict) -> 'Animal':
        return Animal(version = d['version'],
                      class_label = d['class_label'],
                      display_label = d['display_label'],
                      confidence = d['confidence'],
                      model = d['model'],
                      bbox_normalized = BBox.from_dict(d['bbox_normalized']))

@dataclass
class Plant(Object):
    plant_type: str

    @staticmethod
    def from_dict(d: dict) -> 'Plant':
        return Plant(version = d['version'], 
                     class_label = d['class_label'],
                     display_label = d['display_label'],
                     plant_type = d['plant_type'],
                     confidence = d['confidence'],
                     model = d['model'],
                     bbox_normalized = BBox.from_dict(d['bbox_normalized']))

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'class_label': self.class_label,
            'plant_type': self.plant_type,
            'display_label': self.display_label,
            'confidence': self.confidence,
            'model': self.model,
            'bbox_normalized': self.bbox_normalized.to_dict()
        }