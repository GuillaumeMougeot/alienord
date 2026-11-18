from typing import List
from dataclasses import dataclass

from utils.utils import load_config_as_dict
from utils.logging import getLogger

@dataclass
class Bucket:
    name: str

    @staticmethod
    def from_dict(d: dict) -> 'Bucket':
        return Bucket(name = d['name'])

@dataclass
class Cloud:
    IMAGE_EXTENSION: str
    META_EXTENSION: str
    BUCKET_NAME: str
    PATH_TO_FILE: str
    buckets: List[Bucket]

    @staticmethod
    def from_dict(d: dict) -> 'Cloud':
        return Cloud(IMAGE_EXTENSION = d['IMAGE_EXTENSION'],
                     META_EXTENSION = d['META_EXTENSION'],
                     BUCKET_NAME = d['BUCKET_NAME'],
                     PATH_TO_FILE = d['PATH_TO_FILE'],
                     buckets = [Bucket.from_dict(bucket) for bucket in d['buckets']])

@dataclass
class Privacy:
    PUBLISH_THRESHOLD: float
    MODEL_THRESHOLD: float
    MODEL_PATH: str

    @staticmethod
    def from_dict(d: dict) -> 'Privacy':
        return Privacy(PUBLISH_THRESHOLD = d['PUBLISH_THRESHOLD'],
                       MODEL_THRESHOLD = d['MODEL_THRESHOLD'],
                       MODEL_PATH = d['MODEL_PATH'])

@dataclass 
class Logs:
    ENABLED: bool
    LOG_LEVEL: str
    LOG_FILE: str

    @staticmethod
    def from_dict(d: dict) -> 'Logs':
        return Logs(ENABLED = d['ENABLED'],
                    LOG_LEVEL = d['LOG_LEVEL'],
                    LOG_FILE = d['LOG_FILE'])

@dataclass
class Config:
    cloud: Cloud
    privacy: Privacy
    logs: Logs

    @staticmethod
    def from_dict(d: dict) -> 'Config':
        return Config(cloud = Cloud.from_dict(d['cloud']),
                      privacy = Privacy.from_dict(d['privacy']),
                      logs = Logs.from_dict(d['logs']))

config: Config = Config.from_dict(load_config_as_dict())

logger = getLogger(
    level=config.logs.LOG_LEVEL,
    log_file=config.logs.LOG_FILE,
    enabled=config.logs.ENABLED
)