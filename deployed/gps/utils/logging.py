import logging
import os

class GpsLogger(logging.Logger):
    pass


def getLogger(name="root", level = None, enabled = True, just_log_file = False, log_file = None):
    logger = GpsLogger(name, level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s][%(name)s]\t %(message)s")
    if enabled and log_file:
        # in case the log file goes to some nested directory path
        # we want to make sure it exists
        parent_dir = os.path.dirname(log_file)
        os.makedirs(parent_dir, exist_ok=True)
        
        logger.addHandler(logging.FileHandler(log_file))
        logger.handlers[0].setFormatter(formatter)
    if not just_log_file:
        logger.addHandler(logging.StreamHandler())
        logger.handlers[1].setFormatter(formatter)

    return logger

    
