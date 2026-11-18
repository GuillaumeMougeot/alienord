from infra.firebase import Firebase as Database
from infra.gcs import Gcs as CloudConnector
from infra.publisher import PublisherAdapter as Publisher
from infra.cloud_to_db_info import CloudToDatabaseInfo
from infra.search.user_handler import UserHandler
from infra.search.query_handler import QueryHandler
from configuration import config, logger

database = Database()
cloud_connector = CloudConnector(config.cloud.BUCKET_NAME, logger)
cloud_db_adapter = CloudToDatabaseInfo(cloud_connector, config, logger)
publisher = Publisher(cloud_connector, config, logger)

user_handler = UserHandler(database, logger)
query_handler = QueryHandler(database, logger)