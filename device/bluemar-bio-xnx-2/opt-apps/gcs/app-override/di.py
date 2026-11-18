from app.cloud.adapters.gcs import GCS as CloudConnector
from app.configuration import config, logger

cloud_connector = CloudConnector(config.cloud.BUCKET_NAME, config.cloud.SECRETS_PATH, logger)