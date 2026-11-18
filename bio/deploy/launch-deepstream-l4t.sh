#!/bin/bash

export DEVICE_ID=$(hostname)

## check that the media/data folder from the HDD is accessible:
[[ -d /media/data && -x /media/data ]] && 

# start the button push detection
bash launch-button-push.sh &&

# run the pipeline app
docker compose -f docker-compose.yaml up