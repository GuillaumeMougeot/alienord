import os
import cv2
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.di import EventPublisher
from app.configuration import Config
from utils.logging import BioLogger
from adapters import EventNames
from app.components.gps import GpsReader
from core.domain.detection import Batch
from core.domain.pipeline.entities.event import Event
from core.domain.pipeline.events import EventPublisher
from core.infra.adapters.pipeline.pyds.probes.base_probe import ReturnEnum
from core.infra.adapters.pipeline.pyds.probes.batch_event_probe import BatchEventProbe
from core.infra.adapters.pipeline.pyds.events import EventAdapterDTO

@dataclass
class Recording:
    dir: str
    prefix: str
    started: Optional[datetime] = None
    ends: Optional[datetime] = None
    index: int = 0


class RecordProbe(BatchEventProbe):

    def __init__(
        self,
        config: Config,
        logger: BioLogger,
        event_names: List[str],
        event_publisher: EventPublisher,
        event_adapters: Dict[str, EventAdapterDTO]   
    ) -> None:
        
        self.config = config
        self.logger = logger
        self.recording = None
        self.event_names = event_names

        # the event publisher where we subscribe to
        self.event_publisher = event_publisher

        # the event adapters to transform a `Gst.Event` dto back to an `Event`
        self.event_adapters = event_adapters

        # We don't need to send a message back to the application
        self.message_adapters = None
            
    def process_batch(self, batch: Batch) -> ReturnEnum:
        now = datetime.utcnow()

        if not self.recording or self.recording.ends < now:
            return ReturnEnum.OK
        
        for frame in batch.iter_frames():
            if frame.pad_index != 1:
                # we only want to record from the side camera! (pad_index = 1)
                continue 
            
            frame_array = frame.get_array()

            dst_path = os.path.join(
                self.recording.dir,
                f'{self.recording.prefix}_f{self.recording.index:07d}_c{frame.pad_index:02d}.jpg'
            )
                    
            try:
                frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGBA2BGRA)
                cv2.imwrite(filename=dst_path, img=frame_array)
            except Exception as e:
                self.logger.error(f'Error recording the image {dst_path}: {e}')

        self.recording.index += 1
        return ReturnEnum.OK

    def process_event(self, event: Event):
        
        if event.name == EventNames.START_RECORDING:
            self.logger.debug(f'Received start recording event!')
            try:
                gps_data = GpsReader.load_gps_info(self.config.gps.GPS_DATA_PATH)
                ok = GpsReader.check_running_timestamp(gps_data, drift_seconds=10)
            except Exception as e:
                ok = False
                self.logger.error(f'Error loading gps data: {e}')

            geo = gps_data.format_geo() if ok else 'no_gps'
            now = datetime.utcnow()
            
            prefix = self.config.device.DEVICE_ID + '_' + \
                now.strftime(self.config.annotations.FORMATED_UTC_TIMESTAMP)[:-3] + '_' + geo

            self.recording = Recording(
                started=now,
                ends=now+timedelta(seconds=self.config.recordings.RECORDING_SECONDS),
                prefix=prefix,
                dir=os.path.join(
                    self.config.images.PATH, 
                    self.config.recordings.RECORDING_PATH
                )
            )
            self.logger.debug(self.recording)

            try:
                os.makedirs(self.recording.dir, exist_ok=True)
            except Exception as e:
                self.logger.error(f'Error creating {self.recording.dir}: {e}')

            return ReturnEnum.DROP
