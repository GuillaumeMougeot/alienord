import json
import os
from dataclass_wizard import wizard_cli as cli

from utils.utils import *


GENERATED_DIR = os.path.join(SCHEMAS_DIR, 'generated')

###### Script based on:
## https://stackoverflow.com/questions/61483082/what-is-the-proper-way-to-add-type-hints-after-loading-a-yaml-file
######

def generate(merge_config=None, generated_file='schemas/generated/config_model.py'):
    config = load_config_as_dict(merge_config=merge_config)

    with open(os.path.join(CONFIG_DIR, generated_file), 'w') as f:
        code = cli.PyCodeGenerator(file_contents=json.dumps(config), experimental=True).py_code
        # finetune the resulting code
        code = code.replace('Data(JSONWizard)', 'Config(JSONWizard)')
        f.write(code)


if __name__ == '__main__':
    os.makedirs(GENERATED_DIR, exist_ok=True)
    generate(merge_config=None, generated_file=os.path.join(GENERATED_DIR, 'config.py'))
    generate(merge_config='dev', generated_file=os.path.join(GENERATED_DIR, 'config_dev.py'))
