from typing import List
from dataclasses import dataclass

from core.entities.gps import Gps
from core.entities.object import Object

@dataclass
class Meta:
    country: str
    device: str
    camera_index: int
    timestamp: str
    gps: Gps
    objects: List[Object]

    @staticmethod
    def from_dict(d: dict) -> 'Meta':
        return Meta(country = d['country'],
                    device = d['device'],
                    camera_index = d['camera_index'],
                    timestamp = d['timestamp'],
                    gps = Gps.from_dict(d['gps']),
                    objects = [Object.from_dict(obj) for obj in d['objects']])
