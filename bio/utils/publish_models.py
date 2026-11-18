import json
import os
import tarfile
from datetime import datetime
from pprint import pformat
from typing import Union

from utils.logging import getLogger
from utils.utils import *

BUCKET = 'models-bio'


logger = getLogger(
    level='INFO',
    name='PUBLISH_MODELS',
    log_file='logs/publish_models_log.txt',
    just_log_file=True
)

try:
    client = get_storage_client()
except Exception as e:
    logger.error(f"Couldn't init storage client: {e}")
    exit(1)


def get_model_versions():
    """
    Get the model versions from the `models-lock.json`
    """
    lock_file = os.path.join(MODEL_DIR, "models-lock.json")
    try:
        with open(lock_file, "r") as f:
            models = json.load(f)
    except OSError:
        logger.error(f"Couldn't open models-lock.json, does it exist?")
        exit(1)

    return models


def save_model_versions(model_versions):
    """
    Save the new model versions into the `models-lock.json`
    """
    lock_file = os.path.join(MODEL_DIR, "models-lock.json")
    with open(lock_file, "w") as f:
        json.dump(model_versions, f, indent=4)
   

def get_updated_version(model: str, model_dir: str, integrity: str) -> Union[dict, None]:
    """
    Get updated version of a model. Ignores .engine files.

    Args
        model: model name
        model_dir: path to the model
        integrity: the new integrity checksum of the model

    Returns
        If success: A new version of the model, as a dict with keys ('integrity', 'version', 'description', 'resolved')
        If error: None
    """
    logger.info(f'Updating the model {model}')
    print(f"\n\nA newer version of model {model} was found! Let's add it some details...")

    version = input_not_empty('Enter the new version name: ')
    desc = input('Enter a description (optional): ')

    dt = datetime.now().strftime('%Y%m%d%H%M%S')
    fname = f'{dt}_{version}.tgz'
    tmp_fpath = os.path.join(MODEL_DIR, fname)

    print_and_log(f"Compressing the model...")
    # compress the model_dir into the tgz file
    try:
        with tarfile.open(tmp_fpath, 'w:gz') as f:
            f.add(
                model_dir, 
                arcname=model, 
                filter=lambda tar_info: tar_info if '.engine' not in tar_info.name else None
            )
    except Exception as e:
        logger.error(f"Couldn't extract the tgz model file: {e}")
        clean_tmp_file(tmp_fpath)
        return None

    print_and_log(f"Deploying {version} to Google Cloud Storage...")
    # upload the model to GCS
    try:
        resolved = upload_to_gcs(client, BUCKET, tmp_fpath, fname)
        logger.info(f"File {tmp_fpath} uploaded to {resolved}")
    except Exception as e:
        logger.error(f"Couldn't upload {tmp_fpath} to GCS: {e}")
        clean_tmp_file(tmp_fpath)
        return None

    print_and_log(f"Done! It was uploaded to {resolved}\n")

    model_version = dict(integrity=integrity, version=version, description=desc, resolved=resolved)

    clean_tmp_file(tmp_fpath)
    return model_version
    

def print_and_log(txt):
    print(txt)
    logger.info(txt)


def print_and_log_success(success):
    print('\n******** UPDATE INFO ********\n')
    print_and_log(pformat(success))
    print('\n*****************************\n')


def update_model_versions(model_versions: dict):
    models = get_existing_models()

    success = dict()
    for model, model_dir in models:
        integrity = get_checksum(model_dir)

        if model not in model_versions or integrity != model_versions[model]['integrity']:
            # update this model, as the existing version is outdated
            version = get_updated_version(model, model_dir, integrity)
            model_versions[model] = version if version else model_versions.get(model) # the model version may not exist previously
            success[model] = f'updated to {model_versions[model]["version"]}' if version else 'failed to update'
        
        else:
            print(f'Version {model_versions[model]["version"]} of model {model} did not change')
            success[model] = 'unchanged'

    save_model_versions(model_versions)
    print_and_log_success(success)


if __name__ == "__main__":
    model_versions = get_model_versions()
    update_model_versions(model_versions)