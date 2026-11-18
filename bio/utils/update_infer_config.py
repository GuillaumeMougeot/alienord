import os
import re
from argparse import ArgumentParser

import yaml

from utils.utils import CONFIG_DIR, load_config_as_dict


def update_config_yaml(model_name: str, unique_id: int = None):
    if not (unique_id and isinstance(unique_id, int)):
        print("unique_id not provided or not an integer")
        return

    print(f'updating linked model {model_name} in config.yaml')

    with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'r') as f:
        txt = f.read()

    regex = f"(infer:\s+(?:.*\n)*?\s+{model_name}:\s+(?:.*\n)*?\s+GIE_UNIQUE_ID:\s+)\d+"
    new_txt = re.sub(regex, r'\g<1>' + str(unique_id), txt)

    with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'w') as f:
        f.write(new_txt)


def update_model_config(model_config_fname: str, unique_id: int = None):
    if not (unique_id and isinstance(unique_id, int)):
        print("unique_id not provided or not an integer")
        return
    
    print(f'updating linked config {model_config_fname}')
    with open(os.path.join(CONFIG_DIR, model_config_fname), 'r') as f:
        txt = f.read()

    regex='(gie-unique-id\s*=\s*)\d+'
    new_txt = re.sub(regex, r'\g<1>' + str(unique_id), txt)

    with open(os.path.join(CONFIG_DIR, model_config_fname), 'w') as f:
        f.write(new_txt)


def list_models_in_yaml():
    conf = load_config_as_dict()
    return list(conf['infer'].keys())


def list_model_txt_configs():
    """
    Find the currently existing model txt configs. We skip any txt label files.
    """
    return [
        txt_filename for txt_filename in os.listdir(CONFIG_DIR)
        if txt_filename.endswith('txt') and 'label' not in txt_filename
    ]

def find_matching_model_for_txt(models, txt_filename):
    """
    Find the matching model in the config based on the model txt file.
    """
    sorted_models = sorted(models, key=lambda name: len(name), reverse=True)
    return next((model for model in sorted_models if model in txt_filename), None)

def find_matching_txt_for_model(model, txt_filenames):
    """
    Find the matching model txt file based on the model name from the config.
    """
    return next((txt_filename for txt_filename in txt_filenames if model in txt_filename), None)


def read_unique_id_from_txt(txt_filename):
    regex='gie-unique-id\s*=\s*(\d+)'
    with open(os.path.join(CONFIG_DIR, txt_filename), 'r') as f:
        txt = f.read()

    m = re.search(regex, txt)
    if m.lastindex == 1:
        unique_id = m.group(1)
        return int(unique_id)

    return None

def read_models_from_yaml(yaml_filename):
    with open(os.path.join(CONFIG_DIR, yaml_filename), 'r') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    
    return conf['infer']



if __name__=='__main__':
    parser = ArgumentParser(description='Update infer configuration files when one of them changes, to keep them in sync.')

    parser.add_argument('file', type=str, help='File that changed (to be used as ground truth).')
    args = parser.parse_args()


    if args.file.endswith('txt'):
        # match the existing models against this txt file that changed 
        existing_models = list_models_in_yaml()
        model = find_matching_model_for_txt(existing_models, args.file)
        unique_id = read_unique_id_from_txt(args.file)
        update_config_yaml(model, unique_id)

    if args.file.endswith('yaml') or args.file.endswith('yml'):
        existing_txt_filenames = list_model_txt_configs()
        models = read_models_from_yaml(args.file)

        # we need to loop over all the models in the yaml file
        # and update the linked txt model files accordingly
        for name, model in models.items():
            txt = find_matching_txt_for_model(name, existing_txt_filenames)
            update_model_config(txt, model.get('GIE_UNIQUE_ID'))