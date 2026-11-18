from abc import ABC, abstractmethod

class CloudConnector(ABC):
    
    @abstractmethod
    def upload_blob(src_file: str, dest_blob: str) -> None:
        raise NotImplementedError