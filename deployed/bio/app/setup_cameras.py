from typing import List, Tuple
from schemas.generated.config import Camera
from dataclasses import asdict
import subprocess

###############
## This script sets up the cameras with their respective configuration.
## It exits with code 0 if everything went well.
## It exits with code 1 if any camera setup failed.
## Error logs will be found inside the LOG_FILE that is configured for the pipeline.
###############


# these are the error messages we can expect from the arv-tool-0.8
ERROR_MESSAGES = ['error', 'not_found', "can't connect", 'timeout']

def get_output(stdout: bytes, stderr: bytes):
    """
    Return formatted output string from stdout and stderr (bytes).
    """
    out = stdout.decode()
    err = stderr.decode()
    if err:
        return out + '\n' + err
    return out


def find_errors(output: str) -> List[str]:
    lines_with_errors = [line for line in output.split('\n') if any(err_msg in line.lower() for err_msg in ERROR_MESSAGES)]
    return lines_with_errors


def setup_camera(cam: Camera) -> Tuple[bool, str]:
    """
    Setup configuration for the camera given by `src`. 
    
    Returns
    -------
    True if success, False if error.
    """
    name = cam.name
    features = asdict(cam.features)

    feature_str = ' '.join(str(k) + '=' + str(v) for k,v in features.items())
    cmd = f'arv-tool-0.8 -n "{name}" control {feature_str}'
    res = subprocess.run(cmd, shell=True, capture_output=True)

    output = get_output(res.stdout, res.stderr)
    errors = find_errors(output)

    if errors:
        msg = f'Error(s) setting up the camera "{name}":\n' + '\n'.join(errors)
        return (False, msg) 

    return (True, f'Successfully configured camera {name}')
