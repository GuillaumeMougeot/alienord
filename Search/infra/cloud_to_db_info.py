import os
from dataclasses import dataclass
from cloudevents.http.event import CloudEvent

from core.entities import AnnotationType, Meta, Recording, Detection, Gps, Latitude, Longitude, DatabaseInfo
from core.cloud_connector import CloudConnector
from configuration import Config
from utils.logging import SearchLogger
from utils.utils import load_meta_as_dict


@dataclass
class CloudEventInfo:
    blob: str
    file_extension: str
    gcs_url: str
    upload_timestamp: str
    device: str
    camera: int
    timestamp: str
    annotation_type: AnnotationType
    gps: Gps

class CloudToDatabaseInfo:
    
    def __init__(self, cloud_connector: CloudConnector, conifg: Config, logger: SearchLogger):
        self.cloud_connector = cloud_connector
        self.config = conifg
        self.logger = logger

    def get_data_from_cloud_event(self, cloud_event: CloudEvent) -> CloudEventInfo:
        
        path, extension = os.path.splitext(cloud_event.data["name"])
        name = os.path.basename(path)
        extension = extension[1:]
        format = name.split('_')
        gcs_url = f"gs://{cloud_event.data['bucket']}/{path}.{self.config.cloud.IMAGE_EXTENSION}"
        upload_timestamp = cloud_event.data["timeCreated"].replace("-", "").replace(":","")[:-1]

        annotation_type = None
        for bucket in self.config.cloud.buckets:
            if bucket.name in path and AnnotationType.RECORDING.value in bucket.name:
                annotation_type = AnnotationType.RECORDING
                break
            elif bucket.name in path:
                annotation_type = AnnotationType.DETECTION
                break

        gps = None
        if 'no' not in format and 'gps' not in format:
            gps = Gps(speed_kmh = None,
                      course = None, 
                      timestamp = None,
                      latitude = Latitude.geo_to_coordinate(format[2]),
                      longitude = Longitude.geo_to_coordinate(format[3]))
            
        return CloudEventInfo(blob = cloud_event.data["name"], 
                              file_extension = extension,
                              gcs_url = gcs_url,
                              upload_timestamp = upload_timestamp,
                              device = format[0],
                              camera = int(format[-1][1:]),
                              timestamp = format[1],
                              annotation_type = annotation_type,
                              gps = gps)

    def cloud_event_to_recording(self, data: CloudEventInfo) -> Recording:

        return Recording(annotation_type = AnnotationType.RECORDING,
                         image_gs_url = data.gcs_url,
                         country = None,
                         device = data.device,
                         camera_index = data.camera,
                         picture_timestamp = data.timestamp,
                         uploaded_timestamp = data.upload_timestamp,
                         gps = data.gps
                         )

    def cloud_event_to_detection(self, data: CloudEventInfo, detection: Detection) -> Detection:
        
        plant_type = set()
        if data.file_extension == self.config.cloud.META_EXTENSION:
            self.cloud_connector.download_file(data.blob, self.config.cloud.PATH_TO_FILE)
            meta = Meta.from_dict(load_meta_as_dict(self.config.cloud.PATH_TO_FILE))
            for obj in meta.objects:
                if 'animal' in obj.class_label.lower():
                    detection.animal = True
                elif 'plant' in obj.class_label.lower():
                    detection.plant = True
                    plant_type.add(obj.plant_type)
            
            detection.plant_type = list(plant_type) 
            detection.image_gs_url = data.gcs_url
            detection.country = meta.country
            detection.device = meta.device
            detection.camera_index = meta.camera_index
            detection.picture_timestamp = meta.timestamp
            detection.uploaded_timestamp = data.upload_timestamp
            detection.gps = meta.gps
            detection.meta_complete = True
            detection.objects = meta.objects
        elif data.file_extension == self.config.cloud.IMAGE_EXTENSION:
            detection.image_gs_url = data.gcs_url
            detection.device = data.device
            detection.camera_index = data.camera
            detection.picture_timestamp = data.timestamp
            detection.uploaded_timestamp = data.upload_timestamp
            detection.gps = data.gps
            detection.image_complete = True    
        
        return detection
    
    def get_db_info(self, cloud_event: CloudEvent) -> DatabaseInfo:
        
        data = self.get_data_from_cloud_event(cloud_event)
        if data.annotation_type == AnnotationType.RECORDING:
            return self.cloud_event_to_recording(data)
        elif data.annotation_type == AnnotationType.DETECTION:
            detection = Detection(annotation_type = AnnotationType.DETECTION)
            return self.cloud_event_to_detection(data, detection)
        else:
            return None
        