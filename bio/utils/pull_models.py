import json
import os
import shutil
import tarfile
from pprint import pformat
from google.cloud.storage import Client

from utils.logging import getLogger
from utils.utils import *


logger = getLogger(
    level='INFO',
    name='PULL_MODELS',
    log_file='logs/pull_models_log.txt'
)

def get_google_cloud_client():
    try:
        return get_storage_client()
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


def pull_model(client: Client, model: str, model_version: dict) -> bool:
    """
    Pulls the model specified by `model_version` dict.
    It downloads and extracts the model .tgz file into the `model` directory.
    
    Returns: 
        Boolean indicating success.
    """
    uri = model_version['resolved']
    tmp_fname = os.path.basename(uri)
    tmp_fpath = os.path.join(MODEL_DIR, tmp_fname)

    # download the tgz file
    with open(tmp_fpath, 'wb') as f:
        try:
            client.download_blob_to_file(uri, f)
        except Exception as e:
            logger.error(f"Couldn't download the model: {e}\nThis is the model version: {pformat(model_version)}")
            clean_tmp_file(tmp_fpath)
            return False

    
    # extract the tgz into its destination dir
    try:
        with tarfile.open(tmp_fpath, 'r:gz') as f:
            # sanity checks to verify the folder that files will be extracted to matches the model
            filenames = [m.name for m in f.getmembers()]
            for name in filenames:
                assert name.startswith(model)

            f.extractall(MODEL_DIR)

    except AssertionError as e:
        logger.error(f"The tgz model file is not properly structured! This is the list of files it contains:\n{pformat(filenames)}")
        clean_tmp_file(tmp_fpath)
        return False
    except Exception as e:
        logger.error(f"Couldn't extract the tgz model file: {e}")
        clean_tmp_file(tmp_fpath)
        return False

    clean_tmp_file(tmp_fpath)
    return True


def remove_model(model: str, model_dir: str) -> bool:
    """
    Removes the model directory and its contents.
    
    Returns:
        Boolean indicating success.
    """
    try:
        shutil.rmtree(model_dir)
    except Exception as e:
        logger.error(f"Couldn't remove the model {model}: {e}")
        return False

    logger.info(f"Removed '{model}' model as it is not used anymore.")
    return True


def pull_models(gc_client: Client, model_versions: dict):
    """
    Sync the models folder based on the `model_versions` dict.
    
    It will pull a model if:
        - it doesn't exist
        - it exists but the integrity checksum is different
    
    It will remove an existing model if:
        - it doesn't appear in the model_versions, meaning it is not used anymore.
    """
    models = get_existing_models()

    success = dict()
    for model, model_dir in models:
        integrity = get_checksum(model_dir)

        if model in model_versions and integrity != model_versions[model]['integrity']:
            # pull this model, as the existing version is outdated
            # but first, remove the existing outdated version
            ok = remove_model(model, model_dir) and pull_model(gc_client, model, model_versions[model])
            success[model] = f'updated to {model_versions[model]["version"]}' if ok else 'failed to update'

        elif model not in model_versions:
            # remove the model, as it is not used anymore
            ok = remove_model(model, model_dir)
            success[model] = 'removed' if ok else 'failed to remove'

        else:
            success[model] = 'unchanged'

        # remove the processed model - it may not exist, so we add a default to avoid an Exception
        model_versions.pop(model, None)

    # so far we are missing the case where the model does not exist previously! 
    # we treat that case too
    for model, model_version in model_versions.items():
        # all the model versions in here do not exist, so we always pull them
        ok = pull_model(gc_client, model, model_version)
        success[model] = f'pulled {model_version["version"]}' if ok else 'failed to pull'

    logger.info('******** SYNC INFO ********')
    logger.info(pformat(success))
    logger.info('***************************')

    return success
        

if __name__ == "__main__":
    gc_client = get_google_cloud_client()
    model_versions = get_model_versions()
    pull_models(gc_client, model_versions)