import signal
from time import time, sleep
from app.uploader import Uploader
from app.configuration import config, logger
from app.di import cloud_connector

def save_heartbeat():
    with open(config.heartbeat.SINK, 'w') as f:
        f.write(str(round(time()*1000)))

def signal_handler():
    save_heartbeat()
    signal.alarm(config.heartbeat.SECONDS)

def upload_to_gcs(uploader: Uploader):  
    try:
        uploader.start_cycle()
        for directory in config.cloud.directories:
            uploader.upload_and_remove_files_in_directory(directory.name)

        logger.info("Upload finished!")
    except Exception as e:
        logger.error(f'Error: {e}')

if __name__ == '__main__':

    uploader = Uploader(cloud_connector, config, logger)
    signal.signal(signal.SIGALRM, lambda sig, f: signal_handler())
    signal.alarm(config.heartbeat.SECONDS)

    while True:
        try:
            logger.info('Starting to upload to Google Cloud Storage')
            upload_to_gcs(uploader)
            logger.info(f'Done! Waiting {config.cloud.MINUTES} minutes ...')
            sleep_time = config.cloud.MINUTES*60
            sleep(sleep_time)
        except Exception as e:
            logger.error(f'Error: {e}')
            break
    
    # Cancel any scheduled alarm
    signal.alarm(0)