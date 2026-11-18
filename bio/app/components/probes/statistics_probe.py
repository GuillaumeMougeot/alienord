from app.configuration import Config
from utils.logging import BioLogger
from core.domain.detection import Obj, Batch
from core.infra.adapters.pipeline.pyds.probes.batch_probe import BatchProbe
from core.infra.adapters.pipeline.pyds.probes.base_probe import ReturnEnum

class StatisticsProbe(BatchProbe):
    
    def __init__(self, config: Config, logger: BioLogger):
        self.config = config
        self.logger = logger
        self.total_animal_detections = 0
        self.detections_frame = 0

        # We don't need to send a message back to the application
        self.message_adapters = None
    
    def is_dead_animal(self, obj: Obj):
        return obj.gie_unique_id == self.config.infer.roadkill.GIE_UNIQUE_ID

    def is_plant(self, obj: Obj):
        return obj.gie_unique_id == self.config.infer.plant.GIE_UNIQUE_ID
    
    def gather_statistics(self, frame_num: int , obj: Obj):
        if self.is_dead_animal(obj):
            self.logger.info(f'Frame {frame_num}: dead animal detected with confidence {obj.confidence}')
            self.total_animal_detections += 1
            global animal_counter
            animal_counter += 1
        elif self.is_plant(obj):
            self.logger.info(f'Frame {frame_num}: Plant {obj.label} detected')
            with open(self.config.statistics.PATH, 'a') as f:
                f.write(f'{frame_num} {obj.label}\n')

    def process_batch(self, batch: Batch) -> ReturnEnum:
        for frame in batch.iter_frames():
            global animal_counter
            animal_counter = 0
            for obj in frame.iter_objects():
                self.gather_statistics(frame.frame_num, obj)
            if animal_counter >= 1:
                self.detections_frame += 1
        
        self.logger.info(f'Number of frames with at least one dead animal detection: {self.detections_frame}')
        self.logger.info(f'Total number of dead animal detections: {self.total_animal_detections}')

        return ReturnEnum.OK