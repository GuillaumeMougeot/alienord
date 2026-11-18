import os
import yaml
from mergedeep import merge

BASE_DIR = os.path.dirname(__file__)
SCHEMAS_DIR = os.path.join(os.path.dirname(BASE_DIR), "schemas")
CONFIG_DIR = os.path.join(os.path.dirname(BASE_DIR), "configs")
CLIENT_SECRET = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'secrets', 'nordfou-biodiversity-2cd0fb3af162.json')


def load_config_as_dict(merge_config=None) -> dict:
    """
    Load yaml config.

    Arguments
    --------
    merge_config (default = None): Merge another config on top of the regular config file. Disabled if None.
    
    Returns
    --------
    A dictionary
    """
     
    with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'r') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    
    if merge_config:
        with open(os.path.join(CONFIG_DIR, f'{merge_config}.yaml'), 'r') as f:
            dev = yaml.load(f, Loader=yaml.FullLoader)
        merge(conf, dev)
    
    return conf