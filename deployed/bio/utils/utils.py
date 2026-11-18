import os
import yaml
import json
import hashlib
from mergedeep import merge
from google.cloud.storage import Client


BASE_DIR = os.path.dirname(__file__)
SCHEMAS_DIR = os.path.join(os.path.dirname(BASE_DIR), "schemas")
CONFIG_DIR = os.path.join(os.path.dirname(BASE_DIR), "configs")
MODEL_DIR = os.path.join(os.path.dirname(BASE_DIR), "models")
CLIENT_SECRET = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'secrets', 'nordfou-biodiversity-2cd0fb3af162.json')


algo = hashlib.sha512


def file_as_blockiter(fpath, blocksize=65536):
    """
    Read a file in blocks. 
    """
    with open(fpath, 'rb') as f:
        block = f.read(blocksize)
        while len(block) > 0:
            yield block
            block = f.read(blocksize)


def get_checksum(model_dir):
    """
    Get the checksum of a model directory by walking over all the files in a topdown fashion.
    Ignore all the .engine files.
    """
    hash = algo()
    for dirpath, dirnames, filenames in os.walk(model_dir, topdown=True):
        # provide an ordering that is repeatable 
        dirnames.sort()
        filenames.sort()
        for fname in filenames:
            if '.engine' not in fname:
                fpath = os.path.join(dirpath, fname)
                for block in file_as_blockiter(fpath):
                    hash.update(block)
    return hash.name + '-' + hash.hexdigest()


def get_existing_models():
    """
    Returns a list of pairs (model_name, model_dirpath) for the existing models.
    """
    _, dirnames, _ = next(os.walk(MODEL_DIR), (None, [], []))
    return [(dirname, os.path.join(MODEL_DIR, dirname)) for dirname in dirnames]


def input_not_empty(ask: str) -> str:
    """
    Ask for a mandatory input, that cannot be empty.
    """
    res = input(ask)
    while not res.strip():
        res = input(ask)

    return res


def clean_tmp_file(tmp_fpath):
    """
    Clean a temporary file that may not exist.
    """
    try:
        os.remove(tmp_fpath)
    except OSError:
        pass


def get_storage_client():
    """
    Get a client to GCS
    """
    return Client.from_service_account_json(CLIENT_SECRET)



def upload_to_gcs(client: Client, bucket_name: str, fpath: str, destination_blob_name: str) -> str:
    # The google cloud storage Client
    # client
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # fpath = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(fpath)

    return f"gs://{bucket_name}/{destination_blob_name}"

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

def load_device_config_as_dict(path_to_config: str) -> dict:
    with open(path_to_config, 'r') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    
    return conf

def get_models_info() -> dict:
    with open(os.path.join(MODEL_DIR, "models-lock.json"), "r") as f:
        models_info = json.load(f)

    return models_info