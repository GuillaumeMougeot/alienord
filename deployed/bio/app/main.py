import os
import signal
import sys
import logging
from .configuration import config
from utils.logging import getLogger, LoggerWriter

logger = getLogger(
    level=config.logs.LOG_LEVEL,
    log_file=config.logs.LOG_FILE,
    enabled=config.logs.ENABLED
    )
sys.stderr = LoggerWriter(logger, logging.ERROR)

from .di import EventPublisher,  PipelineBuilder
from adapters import event_adapters, EventNames
from .setup_cameras import setup_camera
from app.pipelines import CollectionPipelineFactory, InferencePipelineFactory
from core.infra.adapters.pipeline.pyds.controller import Controller
from core.infra.adapters.pipeline.pyds.driver import Driver
from core.domain.pipeline.events import Event

def configure_cameras():
    if config.source.CAMERA_ON:
        all_ok = True
        for cam in config.source.cameras:
            all_ok, msg = setup_camera(cam)
            logger.info(f'{msg}')
        if not all_ok:
            logger.error(f'{msg}')
            exit(1)

def share_pid():
    with open(config.pid.PATH, 'w') as f:
        f.write(f'{os.getpid()}')

def remove_pid():
    # delete pid
    os.remove(config.pid.PATH)

def main():

    
    # Create driver
    driver = Driver(config = config,
                    logger = logger)

    # Create event publisher
    publisher = EventPublisher(event_adapters, logger)
    
    # Create Pipeline builder
    builder = PipelineBuilder(config, logger)

    # Create Pipeline factory
    if config.PIPELINE == 'controller':
        pipeline = CollectionPipelineFactory(config = config, 
                                             builder = builder, 
                                             logger = logger, 
                                             event_publisher = publisher)
    elif config.PIPELINE == 'inference':
        pass

    # Create Pipelines
    pipeline = pipeline.make()

    # Create controlers
    pipeline_controller = Controller(pipeline = pipeline, 
                                     dispatcher = None,
                                     publisher = publisher,
                                     logger = logger)
    pipeline_controller.set_playing()

    controlers = [pipeline_controller]
    driver.set_controllers(controlers)
    
    signal.signal(signal.SIGINT, lambda sig, f: pipeline_controller.end_of_stream())
    signal.signal(signal.SIGUSR1, lambda sig, f: pipeline_controller.publish(Event(EventNames.START_RECORDING)))

    # Run main loop
    driver.run()


if __name__ == '__main__':
    configure_cameras()
    share_pid()
    main()
    remove_pid()