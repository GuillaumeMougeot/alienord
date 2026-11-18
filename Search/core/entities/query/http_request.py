from dataclasses import dataclass, field
from typing import List

@dataclass
class HttpRequestData:
    min_tp: str = None
    max_tp: str = None
    country: List[str] = field(default_factory=list)
    device: List[str] = field(default_factory=list)
    plant_type: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> 'HttpRequestData':
        try:
            min_tp = d['min_tp']
        except KeyError:
            min_tp = None
        
        try:
            max_tp = d['max_tp']
        except KeyError:
            max_tp = None
        
        try:
            country = d['country']
        except KeyError:
            country = []
        
        try:
            device = d['device']
        except KeyError:
            device = []
        
        try:
            plant_type = d['plant_type']
        except KeyError:
            plant_type = []

        return HttpRequestData(min_tp = min_tp,
                               max_tp = max_tp,
                               country = country,
                               device = device,
                               plant_type = plant_type)