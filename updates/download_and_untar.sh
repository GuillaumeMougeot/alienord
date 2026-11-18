#!/bin/bash

### 
### This script should be uploaded to JFrog in every project
###

# Check if the URL argument is provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <appname> <gs://url>"
    exit 1
fi

# Get the app from the first argument and URL from the second
app="$1"
url="$2"
app_path="/opt/updates/$app"


# We download and extract the files into the right folder for the given app

mkdir -p $app_path &&
gcloud storage cp "$url" "$app_path" &&
tar_name=$(ls $app_path | grep .tar) &&
tar -xzf "$app_path/$tar_name" -C $app_path &&
rm "$app_path/$tar_name" &&

echo "Download and extraction completed."
