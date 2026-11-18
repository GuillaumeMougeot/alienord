from abc import ABC, abstractmethod
from typing import List

from core.entities import Object
from core.cloud_connector import CloudConnector
from configuration import Config
from utils.logging import SearchLogger


class Publisher(ABC):

    def __init__(self, cloud_connector: CloudConnector, config: Config, logger: SearchLogger):
        self.cloud_connector = cloud_connector
        self.config = config
        self.logger: SearchLogger = logger
    
    def is_publishable(self, objects: List[Object]) -> bool:
        for obj in objects:
            if obj.confidence >= self.config.privacy.PUBLISH_THRESHOLD:
                self.logger.info(f'There is an object with confidence above threshold!')
                return True
        
        self.logger.info(f'The image should not be published')
        return False
    
    @abstractmethod
    def publish(self, blob: str, path_to_img: str) -> str:
        raise NotImplementedError