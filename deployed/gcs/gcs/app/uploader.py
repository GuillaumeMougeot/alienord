import os
from app.configuration import Config
from utils.logging import GcsLogger
from app.cloud.ports.cloud_connector import CloudConnector

class Uploader:

    def __init__(self, gcs: CloudConnector, config: Config, logger: GcsLogger):
        self.gcs = gcs
        self.config = config
        self.logger = logger

    def upload_and_remove_files_in_directory(self, directory) -> None:
        """Iterate over files in that directory"""

        BASEPATH = os.path.join(self.config.data.PATH, directory)

        if not os.path.isdir(BASEPATH):
            # don't process the directory if it's missing
            self.logger.warning(f"The directory {BASEPATH} does not exist.")
            return
        
        files_to_upload = os.listdir(BASEPATH)

        for filename in files_to_upload:
            f = os.path.join(BASEPATH, filename)
            destination_blob_name = os.path.join(directory, self.config.DEVICE_ID, filename)
            # checking if it is a file
            if os.path.isfile(f):
                try:
                    self.gcs.upload_blob(f, destination_blob_name)
                    os.remove(f)
                except BaseException as be:
                    raise be
    