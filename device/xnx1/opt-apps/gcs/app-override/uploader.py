import os
import shutil
from app.configuration import Config
from utils.logging import GcsLogger
from app.cloud.ports.cloud_connector import CloudConnector

# Debug switches, edited on the host in /opt/apps/gcs/control/upload.conf.
# Re-read at the start of every upload cycle, so changes apply without a restart.
CONTROL_FILE = '/workspaces/gcs/control/upload.conf'
DEFAULTS = {'UPLOAD_ENABLED': True, 'DELETE_AFTER_UPLOAD': True}
TRUE_VALUES = ('1', 'true', 'yes', 'on')
FALSE_VALUES = ('0', 'false', 'no', 'off')

# With DELETE_AFTER_UPLOAD off, uploaded files are moved here (under data.PATH)
# instead of being deleted, so they stay on disk without being uploaded again.
UPLOADED_DIR = 'uploaded'

class Uploader:

    def __init__(self, gcs: CloudConnector, config: Config, logger: GcsLogger):
        self.gcs = gcs
        self.config = config
        self.logger = logger
        self.control = dict(DEFAULTS)

    def read_control(self) -> dict:
        control = dict(DEFAULTS)
        try:
            with open(CONTROL_FILE) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return control

        for line in lines:
            line = line.split('#', 1)[0].strip()
            if '=' not in line:
                continue
            key, value = (part.strip() for part in line.split('=', 1))
            if key not in control:
                self.logger.warning(f"Unknown setting '{key}' in {CONTROL_FILE}, ignored")
            elif value.lower() in TRUE_VALUES:
                control[key] = True
            elif value.lower() in FALSE_VALUES:
                control[key] = False
            else:
                self.logger.warning(f"Invalid value '{value}' for {key} in {CONTROL_FILE}, using default {DEFAULTS[key]}")
        return control

    def start_cycle(self) -> None:
        self.control = self.read_control()
        self.logger.info(
            f"Upload mode: UPLOAD_ENABLED={self.control['UPLOAD_ENABLED']} "
            f"DELETE_AFTER_UPLOAD={self.control['DELETE_AFTER_UPLOAD']}"
        )

    def upload_and_remove_files_in_directory(self, directory) -> None:
        """Iterate over files in that directory"""

        BASEPATH = os.path.join(self.config.data.PATH, directory)

        if not os.path.isdir(BASEPATH):
            # don't process the directory if it's missing
            self.logger.warning(f"The directory {BASEPATH} does not exist.")
            return

        files_to_upload = [name for name in os.listdir(BASEPATH) if os.path.isfile(os.path.join(BASEPATH, name))]

        if not self.control['UPLOAD_ENABLED']:
            if files_to_upload:
                self.logger.info(f"Uploads disabled: leaving {len(files_to_upload)} file(s) in {BASEPATH}")
            return

        for filename in files_to_upload:
            f = os.path.join(BASEPATH, filename)
            destination_blob_name = os.path.join(directory, self.config.DEVICE_ID, filename)

            if not self.gcs.upload_blob(f, destination_blob_name):
                # keep the file so the next cycle retries it
                continue

            if self.control['DELETE_AFTER_UPLOAD']:
                os.remove(f)
            else:
                keep_dir = os.path.join(self.config.data.PATH, UPLOADED_DIR, directory)
                os.makedirs(keep_dir, exist_ok=True)
                shutil.move(f, os.path.join(keep_dir, filename))
