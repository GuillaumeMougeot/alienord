from enum import Enum

class AnnotationType(str, Enum):
    RECORDING = "recording"
    DETECTION = "detection"