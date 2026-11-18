from dataclasses import dataclass, asdict

@dataclass
class BBox:
    left: float
    top: float
    width: float
    height: float

    @staticmethod
    def from_dict(d: dict) -> 'BBox':
        return BBox(left = d['left'],
                    top = d['top'],
                    width = d['width'],
                    height = d['height'])
    
    def to_dict(self) -> dict:
        return asdict(self)