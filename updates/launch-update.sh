#!/bin/bash

source config.conf

gcloud auth activate-service-account --key-file=/var/secrets/nordfou-biodiversity-2cd0fb3af162.json

bash update_init.sh $PATH_TO_DOCKER_APPS $PATH_TO_NON_DOCKER_APPS
bash update_apps.sh