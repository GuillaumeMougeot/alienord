#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <default_jetson_user> <tailscale_token>" 
    exit 1
fi

default_jetson_user="$1"
tailscale_token="$2"

## installing docker
echo "Installing Docker..."

apt update

apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# add user to docker group to allow running docker without sudo
usermod -aG docker $default_jetson_user

echo "Done!"

## install nvidia-docker
echo "Installing NVIDIA-docker..."

apt update
apt-get install -y nvidia-container
service docker restart

echo "Done!"

## install gcloud
echo "Installing GCloud..."

apt update
apt-get install -y apt-transport-https ca-certificates gnupg curl sudo
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

apt update
apt-get install -y google-cloud-cli
gcloud auth configure-docker --quiet europe-west1-docker.pkg.dev
echo "Done!"

## install tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY