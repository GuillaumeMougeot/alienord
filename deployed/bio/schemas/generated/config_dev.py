from __future__ import annotations

from dataclasses import dataclass

from dataclass_wizard import JSONWizard


@dataclass
class Config(JSONWizard):
    """
    Data dataclass

    """
    device: Device
    PIPELINE: str
    sink: Sink
    source: Source
    muxer: Muxer
    infer: Infer
    tracker: Tracker
    tiler: Tiler
    gps: Gps
    images: Images
    recordings: Recordings
    annotations: Annotations
    statistics: Statistics
    heartbeat: Heartbeat
    pid: Pid
    logs: Logs


@dataclass
class Device:
    """
    Device dataclass

    """
    DEVICE_ID: str
    COUNTRY: str
    PATH_TO_DEVICE_CONFIG: str


@dataclass
class Sink:
    """
    Sink dataclass

    """
    FAKESINK: bool
    ONSCREEN: bool
    OUTPUT_FILE: str
    OVERLAY: bool


@dataclass
class Source:
    """
    Source dataclass

    """
    FAKESRC: bool
    CAMERA_ON: bool
    cameras: list[Camera]
    files: list[str]


@dataclass
class Camera:
    """
    Camera dataclass

    """
    name: str
    description: str
    features: Features


@dataclass
class Features:
    """
    Features dataclass

    """
    Width: int
    Height: int
    AcquisitionFrameRate: float
    PixelFormat: str
    AcquisitionFrameRateMode: str
    ExposureAuto: str
    AutoExposureTimeMax: int
    AutoExposureTimeMin: int
    GainAuto: str
    AutoGainMax: float
    BalanceWhiteAuto: str


@dataclass
class Muxer:
    """
    Muxer dataclass

    """
    WIDTH: int
    HEIGHT: int
    FRAME_RATE: int
    BATCHED_PUSH_TIMEOUT_USEC: int


@dataclass
class Infer:
    """
    Infer dataclass

    """
    roadkill: Roadkill
    car: Car
    plant: Plant


@dataclass
class Roadkill:
    """
    Roadkill dataclass

    """
    CONFIG: str
    LABELS: str
    GIE_UNIQUE_ID: int
    VERSION: str


@dataclass
class Car:
    """
    Car dataclass

    """
    CONFIG: str
    LABELS: str
    GIE_UNIQUE_ID: int
    VERSION: str


@dataclass
class Plant:
    """
    Plant dataclass

    """
    CONFIG: str
    LABELS: str
    GIE_UNIQUE_ID: int
    VERSION: str


@dataclass
class Tracker:
    """
    Tracker dataclass

    """
    CONFIG: str


@dataclass
class Tiler:
    """
    Tiler dataclass

    """
    WIDTH: int
    HEIGHT: int


@dataclass
class Gps:
    """
    Gps dataclass

    """
    GPS_DATA_PATH: str
    GPS_SPEED_THRESHOLD: int


@dataclass
class Images:
    """
    Images dataclass

    """
    SAVE_IMAGES: bool
    BLOCK_IMAGE_MEAN_THRESHOLD_MIN: int
    BLOCK_IMAGE_MEAN_THRESHOLD_MAX: int
    PATH: str
    IMAGES_OUTPUT_PATH: str
    IMAGES_METADATA_OUTPUT_PATH: str
    EXCLUSION_ZONE_THRESHOLD: float


@dataclass
class Recordings:
    """
    Recordings dataclass

    """
    RECORDING_SECONDS: int
    RECORDING_PATH: str


@dataclass
class Annotations:
    """
    Annotations dataclass

    """
    VERSION: float | str
    FORMATED_UTC_TIMESTAMP: str


@dataclass
class Statistics:
    """
    Statistics dataclass

    """
    ENABLED: bool
    PATH: str


@dataclass
class Heartbeat:
    """
    Heartbeat dataclass

    """
    SECONDS: int
    SINK: str


@dataclass
class Pid:
    """
    Pid dataclass

    """
    PATH: str


@dataclass
class Logs:
    """
    Logs dataclass

    """
    ENABLED: bool
    LOG_LEVEL: str
    LOG_FILE: str
    VERBOSE_DUMPDATA_LOG: bool
    LOG_SLOW_WAIT_FRAMES: int
