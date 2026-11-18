from core.domain.pipeline import PipelineFactory
from core.domain.pipeline.entities import Pipeline
from app.configuration import Config
from app.components.probes import RecordProbe, DumpDataProbe, StatisticsProbe
from adapters import event_names, event_adapters

class CollectionPipelineFactory(PipelineFactory):

    def make(self) -> Pipeline:
        config: Config = self.config
        builder = self.builder
        logger = self.logger
        publisher = self.event_publisher

        builder.reset()

        self.queue_for_recording = RecordProbe(config, logger, event_names, publisher, event_adapters).wrap(
            builder.make_queue(),
            'sink'
        )
        
        builder.link_many(
            builder.make_muxer(),
            builder.make_queue(),
            builder.make_videoconvert(name='convertor-rgba'),
            builder.make_capsfilter(format='RGBA', name='capsfilter-rgba'),
            builder.make_inference(
                'pgie-roadkill', 
                config.infer.roadkill.CONFIG
            ),
            builder.make_inference(
                'pgie-car',
                config.infer.car.CONFIG
            ),
            builder.make_inference(
                'pgie-plant',
                config.infer.plant.CONFIG
            ),
            StatisticsProbe(config, logger).wrap(
                self.queue_for_recording,
                'sink'
            ),
            DumpDataProbe(config, logger).wrap(
                builder.make_videoconvert(name='convertor-sink'), 
                'sink'
            ),
            *builder.make_logger_elements(enabled=config.logs.ENABLED),
            *builder.make_sink_elements()
        )

        return builder.get_result()