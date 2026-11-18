#!/bin/bash

docker run -it --rm \
    --network=host \
    --runtime=nvidia \
    --hostname=docker \
	--user "$(id -u app):$(id -g app)"\
    --group-add audio --group-add video --group-add i2c --group-add dialout \
    -e GST_PLUGIN_PATH=/usr/local/lib/aarch64-linux-gnu \
    -e ENV=test \
    -e DEVICE_ID=$(hostname)\
    -v /var/shared:/var/shared \
    -v /media:/media \
    -v /opt/apps/deepstream/devices:/opt/apps/deepstream/devices \
    europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base arv-tool-0.8 $@ ;