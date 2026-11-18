#!/bin/bash

if [ $# -ne 0 ]; then
    echo "Usage: $0" 
    exit 1
fi

## Setup jfrog secrets
/etc/connect/service/ConnectAgent --print-token > /var/secrets/jfrog_device_token.txt
chown monitoring:fleet /var/secrets/jfrog_device_token.txt

## gcloud config for the default user
sudo -u $jetson_user gcloud auth configure-docker --quiet europe-west1-docker.pkg.dev
sudo -u $jetson_user gcloud auth activate-service-account --key-file=/var/secrets/nordfou-biodiversity-2cd0fb3af162.json

## Load docker images
docker load -i /var/shared/deepstream.tar
docker load -i /var/shared/gps.tar
docker load -i /var/shared/gcs.tar
docker load -i /var/shared/monitoring.tar
