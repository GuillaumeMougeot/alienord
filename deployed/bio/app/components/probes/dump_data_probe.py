import os
import cv2
import json
import numpy as np
from typing import List
from datetime import datetime

from app.configuration import Config
from utils.logging import BioLogger
from app.components.gps import GpsReader
from app.components.probes.detection import *

from core.domain.geom import BBox
from core.domain.detection import Frame, Obj, Batch
from core.infra.adapters.pipeline.pyds.probes.base_probe import ReturnEnum
from core.infra.adapters.pipeline.pyds.probes.batch_probe import BatchProbe

class DumpDataProbe(BatchProbe):

    def __init__(self, config: Config, logger: BioLogger):
        self.config = config
        self.logger = logger
        self.should_log_batch_idx = 1
        self.check_dirs()

        # We don't need to send a message back to the application
        self.message_adapters = None
    
    def check_dirs(self) -> None:
        if not os.path.isdir(self.config.images.PATH):
            self.logger.warning('No place to save images')
            return

        self.full_img_path = os.path.abspath(os.path.join(self.config.images.PATH, 
                                                          self.config.images.IMAGES_OUTPUT_PATH))
        self.full_meta_path = os.path.abspath(os.path.join(self.config.images.PATH,
                                                           self.config.images.IMAGES_METADATA_OUTPUT_PATH))

        if not os.path.isdir(self.full_img_path):
            self.logger.info(f"Creating directory '{self.full_img_path}'")
            os.makedirs(self.full_img_path)

        if not os.path.isdir(self.full_meta_path):
            self.logger.info(f"Creating directory '{self.full_meta_path}'")
            os.makedirs(self.full_meta_path)
    
    def is_car(self, obj: Obj) -> bool:
        return obj.gie_unique_id == self.config.infer.car.GIE_UNIQUE_ID

    def is_dead_animal(self, obj: Obj) -> bool:
        return obj.gie_unique_id == self.config.infer.roadkill.GIE_UNIQUE_ID
    
    def is_plant(self, obj: Obj) -> bool:
        return obj.gie_unique_id == self.config.infer.plant.GIE_UNIQUE_ID

    def is_interesting(self, obj: Obj) -> bool:
        return self.is_dead_animal(obj) or self.is_plant(obj)
    
    def is_frame_interesting(self, frame: Frame) -> bool:
        for obj in frame.iter_objects():
            if self.is_interesting(obj):
                return True
        
        return False
    
    def get_frame_array(self, frame: Frame) -> np.ndarray:
        frame_arr = frame.get_array()
        frame_arr = cv2.cvtColor(frame_arr, cv2.COLOR_RGBA2BGRA)

        brightness = frame_arr.mean(axis=0).mean(axis=0).mean(axis=0)
                
        if brightness < self.config.images.BLOCK_IMAGE_MEAN_THRESHOLD_MIN:
            self.logger.warning('Image is not bright enough')
            return None

        if brightness > self.config.images.BLOCK_IMAGE_MEAN_THRESHOLD_MAX:
            self.logger.warning('Image is too bright')
            return None

        return frame_arr

    def blur_car(self, img: np.ndarray, bbox: BBox) -> np.ndarray:

        object = img[
            bbox.top:(bbox.top + bbox.height),
            bbox.left:(bbox.left + bbox.width)
        ]

        ksize = (min(object.shape[0], 200), min(object.shape[1], 200))
        if ksize[0] <= 0 or ksize[1] <= 0:
            return object
        
        img[
            bbox.top:(bbox.top + bbox.height),
            bbox.left:(bbox.left + bbox.width)
        ] = cv2.blur(object, ksize)
        
        self.logger.info(f'Bluring car')
        return img
    
    def dump_image_meta(self, img: np.ndarray, data: FrameDetection) -> None:

        name = self.config.device.DEVICE_ID + '_' + data.timestamp + '_' + data.gps.format_geo() + '_c' + \
            f"{data.camera_index:02d}"
        
        full_meta_path = os.path.join(self.full_meta_path, f'{name}.json')
        hdd_image_path = os.path.join(self.full_img_path, f'{name}.jpg')
        
        cv2.imwrite(filename=hdd_image_path, img=img)

        with open(full_meta_path, 'w') as f:
            json.dump(data.to_dict(), f)

    def can_dump(self) -> bool:
        try:
            gps_info = GpsReader.load_gps_info(self.config.gps.GPS_DATA_PATH)
            ok = GpsReader.check_running_timestamp(gps_info, drift_seconds=10)
        except:
            ok = False

        # update flag for logging extra information
        should_log = self.should_log_batch_idx % self.config.logs.LOG_SLOW_WAIT_FRAMES == 0
        if should_log:
            self.should_log_batch_idx = 1
        else:
            self.should_log_batch_idx += 1
        
        if not ok:
            # if gps is not available or too old we don't save results
            if should_log:
                self.logger.info(f"GPS is not available or it's outdated — skipping datadump")
            return False
        
        if gps_info.speed_kmh < self.config.gps.GPS_SPEED_THRESHOLD:
            if should_log:
                self.logger.info(f"Driving too slow - Speed is {gps_info.speed_kmh} km/h")
            return False

        return True

    def add_plant_detection(self, obj: Obj) -> PlantDetection:
        return PlantDetection(version = self.config.annotations.VERSION,
                              class_label = "Plant",
                              plant_type = obj.label,
                              display_label = obj.label.replace('_', ' ').title(),
                              confidence = obj.confidence,
                              model = self.config.infer.plant.VERSION,
                              bbox_normalized = obj.bbox.normalize(self.config.muxer.WIDTH, self.config.muxer.HEIGHT))
    
    def add_animal_detection(self, obj: Obj) -> AnimalDetection:
        return AnimalDetection(version = self.config.annotations.VERSION,
                              class_label = "Dead Animal",
                              display_label = obj.label.replace('_', ' ').title(),
                              confidence = obj.confidence,
                              model = self.config.infer.roadkill.VERSION,
                              bbox_normalized = obj.bbox.normalize(self.config.muxer.WIDTH, self.config.muxer.HEIGHT))
    
    def add_car_detection(self, obj: Obj) -> CarDetection:
        return CarDetection(version = self.config.annotations.VERSION, 
                            class_label = "Car",
                            display_label = obj.label.replace('_', ' ').title(),
                            confidence = obj.confidence,
                            model = self.config.infer.car.VERSION,
                            bbox_normalized = obj.bbox.normalize(self.config.muxer.WIDTH, self.config.muxer.HEIGHT))

    def add_frame_detection(self, frame: Frame, obj_detections: List[ObjectDetection]) -> FrameDetection:
        timestamp = datetime.utcnow().strftime(self.config.annotations.FORMATED_UTC_TIMESTAMP)[:-3]

        return FrameDetection(self.config.device.COUNTRY,
                              self.config.device.DEVICE_ID,
                              frame.pad_index, #camera_index
                              timestamp,
                              GpsReader.load_gps_info(self.config.gps.GPS_DATA_PATH),
                              obj_detections)
    
    def process_batch(self, batch: Batch) -> ReturnEnum:
        
        if not self.can_dump() or not self.config.images.SAVE_IMAGES:
            return ReturnEnum.OK            

        for frame in batch.iter_frames():

            if self.is_frame_interesting(frame):
                frame_array = self.get_frame_array(frame)

                if frame_array is None:
                    continue

                # process objects
                object_detections = []
                for obj in frame.iter_objects():              
                    if self.is_plant(obj):
                        object_detections.append(self.add_plant_detection(obj))
                    
                    if self.is_dead_animal(obj):
                        object_detections.append(self.add_animal_detection(obj))
                    
                    if self.is_car(obj):
                        frame_array = self.blur_car(frame_array, obj.bbox)
                        object_detections.append(self.add_car_detection(obj))

                self.dump_image_meta(frame_array, self.add_frame_detection(frame, object_detections))

        return ReturnEnum.OK