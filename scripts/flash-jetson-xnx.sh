#!/bin/bash

cd cd dependencies/jetson
tar xvf SE70_generic_preload_20230922.tgz
tar xvjf mfi_jetson-xavier-nx-devkit-emmc.tbz2
cd mfi_jetson-xavier-nx-devkit-emmc/
sudo bash ./nvmflash.sh