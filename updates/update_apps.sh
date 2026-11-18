#!/bin/bash

# Check if no arguments are provided
if [ $# -ne 0 ]; then
    echo "Usage: $0" 
    exit 1
fi

updates_path="/opt/updates"
apps_path="/opt/apps"

# Utility function to update a service
function update_service() {
    cp -f "$apps_path/$1/$1.service" /etc/systemd/system
    systemctl enable "$1.service"
    systemctl daemon-reload
}

## get app updates from the updates_path as a list
update_paths=($(find $updates_path -maxdepth 1 -mindepth 1 -type d))

for path in "${update_paths[@]}"; do

    app=$(basename $path)

    # Remove .env file from previous execution, if present
    if [ -f "$apps_path/$app/.env" ]; then
        rm "$apps_path/$app/.env"
    fi

    mv "$path"/* "$apps_path/$app"

    chown -R root:apps "$apps_path/$app"

    rm -r $path

    update_service $app

    echo "Update done for app $app"
done