import os
import functions_framework
from cloudevents.http.event import CloudEvent

from configuration import config, logger
from di import database, cloud_db_adapter, publisher
from utils.utils import get_filename_from_uri

@functions_framework.cloud_event
def bucket_finalized(cloud_event: CloudEvent):

    db_info = cloud_db_adapter.get_db_info(cloud_event)

    if db_info is None:
        logger.warning(f'The file {cloud_event.data["name"]} should not modify the database')
        return

    filename, extension = get_filename_from_uri(db_info.image_gs_url)
    extension = extension[1:]

    if database.exist(db_info.annotation_type.value, filename):
        if db_info.meta_complete == True:
            db_info.image_complete = True
        elif db_info.image_complete == True:
            db_info = database.get_document(db_info.annotation_type.value, filename)
            db_info.image_complete = True
        
        # db_info.image_public_url = publisher.publish(cloud_event.data["name"], db_info.objects)
        database.update(filename, db_info)
    else:
        database.set(filename, db_info)

    try:
        os.remove(config.cloud.PATH_TO_FILE)
    except FileNotFoundError:
        pass

    try:
        os.remove(f'{filename}.jpg')
    except FileNotFoundError:
        pass