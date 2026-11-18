from google.cloud.storage import Client

from core.cloud_connector import CloudConnector
from utils.logging import SearchLogger

class Gcs(CloudConnector):

    def __init__(self, bucket_name: str, logger: SearchLogger):

        self.bucket_name = bucket_name
        self.client = None
        self.base_url = "https://storage.googleapis.com"
        self.logger = logger

        try:
            self.client = Client()
        except Exception as e:
            self.logger.error(f"Couldn't init storage client: {e}")
            exit(1)

    def download_blob(self, source_blob_name: str, fpath: str) -> str:
        """
        Downloads a blob from the bucket.

        Arguments
        --------
        source_blob_name: ID of your GCS object
        fpath: Path to which the file should be downloaded
        
        Returns
        --------
        An URI
        """
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(source_blob_name)
        
        blob.download_to_filename(fpath)
        
        return f'gs://{self.bucket_name}/{source_blob_name}'
    
    def download_file(self, source_blob_name: str, file_path: str):
        try:
            uri = self.download_blob(source_blob_name, file_path)
            self.logger.info(f"File {source_blob_name} downloaded from {uri}")
        except Exception as e:
            self.logger.error(f"Couldn't download {source_blob_name} from GCS: {e}")
    
    def upload_to_gcs(self, fpath: str, destination_blob_name: str) -> str:
        """
        Upload to Google Cloud storage

        Arguments
        --------
        client: The google cloud storage Client
        bucket_name: The ID of your GCS bucket
        fpath: Path to your file to upload
        destination_blob_name: ID of your GCS object

        Returns
        --------
        An URI
        """
       
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(fpath)

        return f"gs://{self.bucket_name}/{destination_blob_name}"
    
    def upload_file(self, source_file_name, destination_blob_name) -> None:
        """
        Uploads a file to the bucket.

        Arguments
        --------
        source_file_name: Path to your file to upload
        destination_blob_name: : ID of your GCS object
        
        """
        try:
            uri = self.upload_to_gcs(source_file_name, destination_blob_name)
            self.logger.info(f"File {source_file_name} uploaded to {uri}")
        except Exception as e:
            self.logger.error(f"Couldn't upload {source_file_name} to GCS: {e}")
    
    def publish_img(self, source_blob_name: str) -> str:
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(source_blob_name)

            blob.make_public()

            return f'{self.base_url}/{self.bucket_name}/{source_blob_name}'
        except Exception as e:
            self.logger.error(f"Couldn't publish the object: {e}")