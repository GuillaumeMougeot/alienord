from __future__ import annotations

from dataclasses import dataclass

from dataclass_wizard import JSONWizard


@dataclass
class Config(JSONWizard):
    """
    Data dataclass

    """
    gps: Gps
    heartbeat: Heartbeat
    logs: Logs


@dataclass
class Gps:
    """
    Gps dataclass

    """
    GPS_DATA_PATH: str
    GPS_GLOB_PATH: str


@dataclass
class Heartbeat:
    """
    Heartbeat dataclass

    """
    SINK: str


@dataclass
class Logs:
    """
    Logs dataclass

    """
    ENABLED: bool
    LOG_LEVEL: str
    LOG_FILE: str
