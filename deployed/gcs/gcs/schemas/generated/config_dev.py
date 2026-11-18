from __future__ import annotations

from dataclasses import dataclass

from dataclass_wizard import JSONWizard


@dataclass
class Config(JSONWizard):
    """
    Data dataclass

    """
    DEVICE_ID: str
    cloud: Cloud
    data: Data
    heartbeat: Heartbeat
    logs: Logs


@dataclass
class Cloud:
    """
    Cloud dataclass

    """
    SECRETS_PATH: str
    BUCKET_NAME: str
    MINUTES: int
    directories: list[Directory]


@dataclass
class Directory:
    """
    Directory dataclass

    """
    name: str


@dataclass
class Data:
    """
    Data dataclass

    """
    PATH: str


@dataclass
class Heartbeat:
    """
    Heartbeat dataclass

    """
    SECONDS: int
    SINK: str


@dataclass
class Logs:
    """
    Logs dataclass

    """
    ENABLED: bool
    LOG_LEVEL: str
    LOG_FILE: str
