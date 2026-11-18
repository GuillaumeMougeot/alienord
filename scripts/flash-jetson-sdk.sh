#!/bin/bash

### this script is expected to be run from the root of the project:
### USAGE: ./scripts/flash-jetson-sdk.sh

L4T_DIR=dependencies/jetson/Linux_for_Tegra

if [[ ! -d $L4T_DIR ]]; then
    echo "Linux_for_Tegra directory not found. Did you download and prepare the sdk?"
    echo "NOTICE: the script must be run from the root of the project:"
    echo "./scripts/flash-jetson-sdk.sh"
    exit 1;
fi

cd $L4T_DIR

sudo bash ./flash.sh jetson-agx-orin-devkit-as-nx-16gb mmcblk0p1
