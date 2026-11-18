from dataclasses import dataclass

from core.entities.bbox import BBox

@dataclass
class PrivacyModelInfo:
    bbox: BBox
    conf: float