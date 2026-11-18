import functions_framework
from cloudevents.http.event import CloudEvent

from di import database_adapter, cloud_connector

@functions_framework.cloud_event
def bucket_deleted(cloud_event: CloudEvent):
    pass