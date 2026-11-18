from abc import ABC, abstractmethod

class CloudConnector(ABC):

    @abstractmethod
    def download_file(self, source_blob_name: str, file_path: str):
        raise NotImplementedError
    
    @abstractmethod
    def upload_file(self, source_file_name: str, destination_blob_name: str):
        raise NotImplementedError

    @abstractmethod
    def publish_img(source_blob_name: str) -> str:
        raise NotImplementedError