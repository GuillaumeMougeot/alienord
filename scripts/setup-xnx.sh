#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <path_to_secrets> <default_jetson_user>" 
    exit 1
fi

path_to_secrets="$1"
default_jetson_user="$2"

###################
## create folders
###################

function create_folders(){
    # Create app folders
    mkdir -p /opt/apps/deepstream
    mkdir -p /opt/apps/deepstream-monitoring
    mkdir -p /opt/apps/camera
    mkdir -p /opt/apps/gps
    mkdir -p /opt/apps/gcs
    mkdir -p /opt/apps/updates

    # Create update folder
    mkdir -p /opt/updates

    # Create shared folders
    mkdir -p /var/shared/heartbeat
    mkdir -p /var/shared/pid
    mkdir -p /var/shared/logs

    # Create secrets folder
    mkdir -p /var/secrets

    # Create secrets folder
    mkdir -p /media/data/meta
    mkdir -p /media/data/images
    mkdir -p /media/data/recordings

    # Create folder for the Github repo
    mkdir -p /opt/code
}

#########################
## setup secrets
#########################

function secrets(){
    # Google cloud secret
    cp "$path_to_secrets/nordfou-biodiversity-2cd0fb3af162.json" /var/secrets/

    # Github bot credentials
    cp "$path_to_secrets/bot.env" /var/secrets/
}

########################
## Install dependencies
########################

function install_dependencies(){
    tailscale_token=$(cat "$path_to_secrets/tailscale.txt")
    sudo bash install-deps.sh $default_jetson_user $tailscale_token
}

#########################
## setup users & groups
#########################

function create_users_groups() {
    # Create groups
    addgroup --system shared
    addgroup --system gcs
    addgroup --system apps
    addgroup --system fleet

    # Create users
    adduser --system --no-create-home --ingroup shared \
        --gecos "Generic account to run apps without extra permissions" \
        --disabled-password --disabled-login app

    adduser --system --no-create-home --ingroup shared \
        --gecos "User that runs the Uploader app" \
        --disabled-password --disabled-login uploader

    adduser --system --no-create-home --ingroup shared \
        --gecos "User that runs the software monitoring app" \
        --disabled-password --disabled-login monitoring

    # Add users to groups
    usermod -a -G apps,audio,video,i2c,dialout,docker app
    usermod -a -G gcs,apps,docker uploader
    usermod -a -G apps,fleet,docker,i2c monitoring
}

#########################
## Install apps
#########################

function download_docker_images(){
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gcs:base
}

function download_and_untar() {
    gcloud storage cp "gs://artifacts-bio/apps/$1" "$2" &&
    tar_name=$(ls $2 | grep .tar) &&
    tar -xzf "$2/$tar_name" -C $2 &&
    rm "$2/$tar_name"
}

function install_apps(){
    gcloud auth activate-service-account --key-file=/var/secrets/nordfou-biodiversity-2cd0fb3af162.json

    download_docker_images

    app_path="/opt/apps/"
    download_and_untar "updates-base.tar.gz" "$app_path/updates"
    download_and_untar "deepstream-base.tar.gz" "$app_path/deepstream"
    download_and_untar "deepstream-monitoring-base.tar.gz" "$app_path/deepstream-monitoring"
    download_and_untar "camera-base.tar.gz" "$app_path/camera"
    download_and_untar "gps-base.tar.gz" "$app_path/gps"
    download_and_untar "gcs-base.tar.gz" "$app_path/gcs"
}

#########################
## setup github project
#########################

function setup_github_project(){
    # source bot github credentials
    source $path_to_secrets/bot.env

    # Set github configuration
    git config --global user.name "$GITHUB_USER"
    git config --global user.email "$GITHUB_EMAIL"
    git config --global credential.helper store

    # clone repository
    cd /opt/code
    git clone https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/trifork/vd-biodiversity.git

    # set remote url
    cd vd-biodiversity
    git remote set-url origin https://${GITHUB_TOKEN}@github.com/trifork/vd-biodiversity.git
}


#########################
## setup services
#########################

function setup_services(){
    cp /opt/apps/updates/updates.service /etc/systemd/system
    cp /opt/apps/deepstream/deepstream.service /etc/systemd/system
    cp /opt/apps/deepstream-monitoring/deepstream-monitoring.service /etc/systemd/system
    cp /opt/apps/camera/camera.service /etc/systemd/system
    cp /opt/apps/gps/gps.service /etc/systemd/system
    cp /opt/apps/gcs/gcs.service /etc/systemd/system

    systemctl enable updates.service
    systemctl enable deepstream.service
    systemctl enable deepstream-monitoring.service
    systemctl enable camera.service
    systemctl enable gps.service
    systemctl enable gcs.service
    systemctl daemon-reload 
}

#########################
## Setup ownerships
#########################

function permissions(){
    chown -R root:shared /var/shared
    chown -R root:shared /media/data
    chown -R root:apps /opt/apps
    chown -R root:apps /opt/updates
    chown uploader:gcs /var/secrets/nordfou-biodiversity-2cd0fb3af162.json

    chmod -R g+w /var/shared
    chmod -R g+w /media/data
}

create_folders
secrets
install_dependencies
create_users_groups
install_apps
setup_services
permissions
setup_github_project