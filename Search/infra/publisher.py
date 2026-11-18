# from ultralytics import YOLO
from typing import List
# import cv2
import os

from core.entities import Object
from core.publisher import Publisher
from core.entities import BBox, PrivacyModelInfo
from utils.utils import get_filename_from_uri

class PublisherAdapter(Publisher):

    def publish(self, blob: str, objects: List[Object]) -> str:
        raise NotImplementedError
        if self.is_publishable(objects):
            filename, _ = get_filename_from_uri(blob)
            path_to_img = f'{filename}.jpg'
            blob = os.path.join('images', '/'.join(blob.split('/')[1:-1]), path_to_img)
            
            self.cloud_connector.download_file(blob, path_to_img)
            blur_objects = self.predict(path_to_img)

            if blur_objects:
                self.blur(path_to_img, blur_objects)
                self.cloud_connector.upload_file(path_to_img, blob)
                return self.cloud_connector.publish_img(blob)
        return None

    def predict(self, path_to_img: str) -> PrivacyModelInfo:
        raise NotImplementedError
        model = YOLO(self.config.privacy.MODEL_PATH)
        results = model.predict(path_to_img)
        
        parsed_results = []
        for r in results:
            parsed_result = self.parse_results(r)
            if parsed_result:
                parsed_results.append(parsed_result)
        
        return parsed_results
    
    def parse_results(self, detection) -> PrivacyModelInfo:
        raise NotImplementedError
        try:
            bbox = detection.boxes.xywh.tolist()[0]
            confidence = detection.boxes.conf.tolist()[0]
            if confidence >= self.config.privacy.MODEL_THRESHOLD:
                return PrivacyModelInfo(bbox = BBox(left = bbox[0] - bbox[2]/2,
                                                    top = bbox[1] - bbox[3]/2,
                                                    width = bbox[2],
                                                    height = bbox[3]),
                                        conf = confidence)
            return None
        except IndexError:
            self.logger.info(f'There is nothing to blur')
            return None

    def blur(self, path_to_img: str, detections: List[PrivacyModelInfo]) -> None:
        raise NotImplementedError
        img = cv2.imread(path_to_img) 
        
        for detection in detections:
            left = int(detection.bbox.left)
            top = int(detection.bbox.top)
            width = int(detection.bbox.width)
            height = int(detection.bbox.height)
            
            object = img[
                top:(top + height),
                left:(left + width)
            ]

            ksize = (min(object.shape[0], 200), min(object.shape[1], 200))
            if ksize[0] <= 0 or ksize[1] <= 0:
                continue

            img[
                top:(top + height),
                left:(left + width)
            ] = cv2.blur(object, ksize)

        cv2.imwrite(filename=path_to_img, img=img)