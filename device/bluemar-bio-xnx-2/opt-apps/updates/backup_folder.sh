#!/bin/bash

### 
### This script should be uploaded to JFrog in every project
###

# Check if arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <appname> <updates|apps>" 
    exit 1
fi

app="$1"
folder="$2"
original_path="/opt/${folder}/$app"
backup_path="/opt/${folder}_backup/$app"

# Check if the updates path exists
if [ ! -d "$original_path" ]; then
    echo "Directory $original_path does not exist, backup is not needed."
    exit 0
fi


# create the backup directory if needed
mkdir -p $backup_path &&

# clean the backup directory before we do a new backup
rm -r $backup_path &&

# backup the current updates/apps path
mv $original_path $backup_path &&

echo "Backup done for directory $original_path"
