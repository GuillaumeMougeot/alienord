#!/bin/bash

####################
## Utility functions
####################

function get_apps() {
    paths=("$@")
    for path in "${paths[@]}"; do
        echo $path | cut -d'/' -f1
    done | sort -u
}

function get_url() {
    elements=($(gsutil ls gs://artifacts-bio/apps))
    for obj in "${elements[@]}"; do
        if [[ $obj == *$1* ]]; then
            url=$obj
            break
        fi
    done
}

function docker_deploy() {
    app_name=$1
    hash=$(git --no-pager log -n 5 --format="%H" | sed -n '2p')
    echo "App tag: $hash"
    get_url "$app_name-$hash"
    echo "GCS deploy url: $url"
    bash $path_to_backup $app_name updates
    bash $path_to_download_untar $app_name $url
    bash $path_to_docker_pull $app_name $PROJECT
}

function undockerized_deploy(){
    app_name=$1
    hash=$(git --no-pager log -n 5 --format="%H" | sed -n '1p')
    echo "App tag: $hash"
    get_url "$app_name-$hash"
    echo "gcs deploy url: $url"
    bash $path_to_backup $app_name updates
    bash $path_to_download_untar $app_name $url
}

#######
## Main
#######

path_to_backup="$PATH_TO_SCRIPTS/backup_folder.sh"
path_to_download_untar="$PATH_TO_SCRIPTS/download_and_untar.sh"
path_to_docker_pull="$PATH_TO_SCRIPTS/docker_pull.sh"

cd $PATH_TO_CODE

output=$(git pull)

if [[ $output == *"Already up to date."* ]]; then
    echo "No changes detected"
    exit 0
fi

files=($(git --no-pager diff --name-only HEAD@{1} HEAD))

# Get unduplicated app names from modified file list
apps=($(get_apps "${files[@]}"))
echo "Apps to be updated: "

for app in "${apps[@]}"; do
    if cat $PATH_TO_DOCKER_APPS | grep $app >/dev/null; then
        echo "Update dockerized app: $app"
        docker_deploy $app
    elif cat $PATH_TO_NON_DOCKER_APPS | grep $app >/dev/null; then
        echo "Update non docker app: $app"
        undockerized_deploy $app
    else 
        echo "No update needed in: $app"
    fi
    echo "Update done!"
done
