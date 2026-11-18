import os
import yaml
import json

from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(os.path.dirname(BASE_DIR), "configs")
FORMAT = '%Y%m%dT%H%M%S.%f'

def load_config_as_dict() -> dict:
    """
    Load yaml config.
    
    Returns
    --------
    A dictionary
    """
     
    with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'r') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    
    return conf

def load_meta_as_dict(path: str) -> dict:
    """
    Arguments
    --------
    path (str): Path to where the metadata is stored.
    
    Returns
    --------
    A dictionary
    """

    with open(path, 'r') as f:
        conf = json.load(f)
    
    return conf

def get_filename_from_uri(uri: str) -> str:
    """
    Arguments
    --------
    uri (str): URI.
    
    Returns
    --------
    Basename of the uri
    """
    return os.path.splitext(os.path.basename(uri))

def str_to_date(timestamp: str):
    """
    Arguments
    --------
    timestamp (str): Timestamp
    
    Returns
    --------
    datetime object
    """
    return datetime.strptime(timestamp, FORMAT)

def date_to_str(timestamp) -> str:
    """
    Arguments
    --------
    timestamp (Datetime): Timestamp
    
    Returns
    --------
    str representing the timestamp with the format
    """
    return timestamp.strftime(FORMAT)[:-3]
