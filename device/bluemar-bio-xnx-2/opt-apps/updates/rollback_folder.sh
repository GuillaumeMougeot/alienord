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


# Check that the backup path exists
if [ ! -d "$backup_path" ]; then
    echo "Directory $backup_path does not exist."
    exit 1
fi

# create the updates directory and its parents if they doesn't exist (to avoid failing in the next step)
mkdir -p $original_path &&

# clean the updates/apps directory before we rollback with the backup
rm -r $original_path && 

# rollback the backup while deleting the backup folder
mv $backup_path $original_path &&

echo "Rollback done for directory $original_path"


