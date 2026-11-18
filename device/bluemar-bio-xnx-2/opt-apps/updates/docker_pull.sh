#!/bin/bash

### 
### This script should be uploaded to JFrog in every project
###


docker_pull() {

    # Pull a given docker image with retries. 
    # 5 retries with a pause of 1 second between retries.

    # Usage:
    # docker_pull <docker_image> 

    if [ $# -ne 1 ]; then
        echo "Error: No image chosen to be pulled"
        return 1
    fi

    success=0
    pause=1 # seconds between retries
    tries=5 # X attempts
    attempt=0
    while [ $success = 0 -a $attempt -lt $tries ]; do
        echo "Pulling $1 (try $(($attempt+1))/$tries)..."
        docker pull "$1" && success=1 && echo "OK"
        let attempt=attempt+1
        sleep $pause 
    done
    if [ $success = 0 ]; then
        echo "Error: docker pull failed"
        return 1
    fi
} 


# Check if the URL argument is provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <appname> <projectname>" 
    exit 1
fi

# Get the app from the first argument
app="$1"
project_name="$2"
app_path="/opt/updates/$app"

regex="\b(.\S+docker\.pkg\.dev\/$project_name.*\/[\w-]+:[\w-]+)"

# Make sure that $app_path exists
if [ ! -d "$app_path" ]; then
    echo "Directory $app_path does not exist."
    exit 1
fi

# Use the "grep" command to find matches of the regex in the files within the app folder
matches=($(grep --perl-regexp --only-matching --no-filename --recursive "$regex" "$app_path"))

for match in "${matches[@]}"; do
    docker_pull $match || exit 1;
    echo "----------------------------------------------------"
done
