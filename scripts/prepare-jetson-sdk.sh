#!/bin/bash

function read_simple_yaml() {
    # $1: yaml file
    # $2: value to read
    cat $1 | 
    grep "$2:" | 
    sed -E s/"$2:"[[:space:]]+// |   # remove spaces
    sed -E s/^\"// |                 # remove initial "
    sed -E s/\"$// |                 # remove last "
    tr -d '\n'                       # remove newlines
}

L4T_RELEASE_PACKAGE=Jetson_Linux*
SAMPLE_FS_PACKAGE=Tegra_Linux*
JETSON_ACCOUNT=$PWD/secrets/jetson-account.yaml
ENABLE_AUTOLOGIN=1

cd dependencies/jetson
tar xf ${L4T_RELEASE_PACKAGE}
cd Linux_for_Tegra/rootfs/
sudo tar xpf ../../${SAMPLE_FS_PACKAGE}
cd ..
sudo ./apply_binaries.sh


host=$(read_simple_yaml $JETSON_ACCOUNT host)
user=$(read_simple_yaml $JETSON_ACCOUNT username)
password=$(read_simple_yaml $JETSON_ACCOUNT password)
if [ ENABLE_AUTOLOGIN ]; then
    autologin="-a" # this enables autologin for the user
else
    autologin=""
fi

sudo bash tools/l4t_create_default_user.sh -u $user -p $password -n $host $autologin --accept-license

cd rootfs/
path_to_secrets=$(dirname $JETSON_ACCOUNT)
path_to_dependencies="$(dirname "$path_to_secrets")/scripts"
sudo bash scripts/pre-flash.sh $path_to_secrets $path_to_dependencies $user