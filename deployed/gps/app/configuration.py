import os
from utils.utils import load_config_as_dict
from utils.logging import getLogger


IS_DEV = os.environ['ENV'] == 'dev'
IS_TEST = os.environ['ENV'] == 'test'
        

if IS_DEV:
    from schemas.generated.config_dev import *
    from schemas.generated.config_dev import Config
    merge_config = 'dev'
else:
    from schemas.generated.config import *
    from schemas.generated.config import Config
    merge_config = None


config: Config = Config.from_dict(load_config_as_dict(merge_config=merge_config))

logger = getLogger(
    name='GPS',
    level=config.logs.LOG_LEVEL,
    log_file=config.logs.LOG_FILE,
    enabled=config.logs.ENABLED
)