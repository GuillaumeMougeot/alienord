import os

from utils.utils import load_config_as_dict, load_device_config_as_dict, get_models_info

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
config.device.DEVICE_ID = os.environ.get('DEVICE_ID')

models_info = get_models_info()
config.infer.car.VERSION = models_info['car']['version']
config.infer.roadkill.VERSION = models_info['roadkill']['version']
# config.infer.plant.VERSION = models_info['plant']['version']

if config.source.CAMERA_ON:
    path_to_config = os.path.join(config.device.PATH_TO_DEVICE_CONFIG, f'{config.device.DEVICE_ID}.yaml')
    device_config = load_device_config_as_dict(path_to_config)

    config.device.COUNTRY = device_config['COUNTRY']

    for cam in config.source.cameras:
        cam.name = device_config[cam.description]
