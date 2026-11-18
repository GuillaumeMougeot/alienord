from google.cloud.storage import Client
from app.cloud.ports.cloud_connector import CloudConnector
from utils.logging import GcsLogger

class GCS(CloudConnector):
    
    def __init__(self, bucket_name: str, secrets: str, logger: GcsLogger):

        self.bucket_name = bucket_name
        self.secrets = secrets
        self.logger = logger
        
        try:
            self.client = Client.from_service_account_json(self.secrets)
        except Exception as e:
            self.logger.error(f"Couldn't init storage client: {e}")
            exit(1)
    
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
    
    def upload_blob(self, source_file_name, destination_blob_name) -> bool:
        """
        Uploads a file to the bucket.

        Arguments
        --------
        source_file_name: Path to your file to upload
        destination_blob_name: : ID of your GCS object

        Returns
        --------
        True if the upload succeeded, False if it failed (the error is logged)
        """
        try:
            uri = self.upload_to_gcs(source_file_name, destination_blob_name)
            self.logger.info(f"File {source_file_name} uploaded to {uri}")
            return True
        except Exception as e:
            self.logger.error(f"Couldn't upload {source_file_name} to GCS: {e}")
            return False
    
