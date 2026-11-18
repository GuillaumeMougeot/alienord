#!/bin/bash

# Check if arguments are provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <appname>" 
    exit 1
fi

app="$1"

# Stop, disable and remove service
systemctl stop "$app.service"
systemctl disable "$app"
rm "/etc/systemd/system/$app.service"