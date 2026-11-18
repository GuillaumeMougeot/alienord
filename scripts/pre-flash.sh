#!/bin/bash

if [ $# -ne 3 ]; then
    echo "Usage: $0 <path_to_secrets> <path_to_dependencies> <default_jetson_user>" 
    exit 1
fi

path_to_secrets="$1"
path_to_dependencies="$2"
default_jetson_user="$3"


######################
## Mount directories
######################

function mount_folders(){
    mount --rbind /sys ./sys
    mount --rbind /proc ./proc
    mount --rbind /dev ./dev
}

###################
## create folders
###################

function create_folders(){

    
    LC_ALL=C chroot . bash -c '
    
    # Create app folders
    mkdir -p /opt/apps/deepstream
    mkdir -p /opt/apps/deepstream-monitoring
    mkdir -p /opt/apps/camera
    mkdir -p /opt/apps/gps
    mkdir -p /opt/apps/gcs
    mkdir -p /opt/apps/monitoring

    # Create update folder
    mkdir -p /opt/updates

    # Create scripts folder
    mkdir -p /opt/scripts

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
    
    # Create file with apps to monitor
    echo -e "deepstream\ngps\ngcs" > /var/shared/apps_to_monitor.txt
    '
}

#########################
## setup secrets
#########################

function secrets(){
    # Google cloud secret
    cp "$path_to_secrets/nordfou-biodiversity-2cd0fb3af162.json" ./var/secrets/

    # Jfrog user token
    cp "$path_to_secrets/jfrog_user_token.txt" ./var/secrets/
}

########################
## Install dependencies
########################

function install_dependencies(){
    cp "$path_to_dependencies/install-deps.sh" ./tmp
    LC_ALL=C chroot . bash /tmp/install-deps.sh $default_jetson_user
    cp "$path_to_dependencies/setup.sh" ./opt/scripts
}

#########################
## setup users & groups
#########################

function create_users_groups() {
    
    LC_ALL=C chroot . bash -c '
    
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
    '
}

#########################
## Install apps
#########################

function download_docker_images(){
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gcs:base
    docker pull europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/monitoring:base
}

function save_imgs(){
    docker save -o ./var/shared/deepstream.tar europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base
    docker save -o ./var/shared/gps.tar europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base
    docker save -o ./var/shared/gcs.tar europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gcs:base
    docker save -o ./var/shared/monitoring.tar europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/monitoring:base
}

function install_apps(){
    echo "Downloading docker images"
    download_docker_images
    echo "Saving docker images"
    save_imgs

    LC_ALL=C chroot . bash -c '

    gcloud auth activate-service-account --key-file=/var/secrets/nordfou-biodiversity-2cd0fb3af162.json

    function download_and_untar() {
        gcloud storage cp "gs://artifacts-bio/apps/$1" "$2" &&
        tar_name=$(ls $2 | grep .tar) &&
        tar -xzf "$2/$tar_name" -C $2 &&
        rm "$2/$tar_name"
    }

    app_path="/opt/apps/"
    download_and_untar "jfrog-scripts.tar.gz" "/opt/scripts"
    download_and_untar "deepstream-base.tar.gz" "$app_path/deepstream"
    download_and_untar "deepstream-monitoring-base.tar.gz" "$app_path/deepstream-monitoring"
    download_and_untar "camera-base.tar.gz" "$app_path/camera"
    download_and_untar "gps-base.tar.gz" "$app_path/gps"
    download_and_untar "gcs-base.tar.gz" "$app_path/gcs"
    download_and_untar "monitoring-base.tar.gz" "$app_path/monitoring"
    '
}

#########################
## setup services
#########################

function setup_services(){
    
    LC_ALL=C chroot . bash -c '

    cp /opt/scripts/updates.service /etc/systemd/system
    cp /opt/apps/deepstream/deepstream.service /etc/systemd/system
    cp /opt/apps/deepstream-monitoring/deepstream-monitoring.service /etc/systemd/system
    cp /opt/apps/camera/camera.service /etc/systemd/system
    cp /opt/apps/gps/gps.service /etc/systemd/system
    cp /opt/apps/gcs/gcs.service /etc/systemd/system
    cp /opt/apps/monitoring/monitoring.service /etc/systemd/system

    systemctl enable updates.service
    systemctl enable deepstream.service
    systemctl enable deepstream-monitoring.service
    systemctl enable camera.service
    systemctl enable gps.service
    systemctl enable gcs.service
    systemctl enable monitoring.service
    '
}

#########################
## Setup ownerships
#########################

function permissions(){

    LC_ALL=C chroot . bash -c '

    chown -R root:shared /var/shared
    chown -R root:shared /media/data
    chown -R root:apps /opt/apps
    chown -R root:apps /opt/updates
    chown uploader:gcs /var/secrets/nordfou-biodiversity-2cd0fb3af162.json
    chown monitoring:fleet /var/secrets/jfrog_user_token.txt
    # chown monitoring:fleet /var/secrets/jfrog_device_token.txt
    chown monitoring:fleet /var/shared/apps_to_monitor.txt

    chmod -R g+w /var/shared
    chmod -R g+w /media/data
    '
}

mount_folders
create_folders
secrets
install_dependencies
create_users_groups
install_apps
setup_services
permissions