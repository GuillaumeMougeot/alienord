FROM nvcr.io/nvidia/deepstream:6.2-devel AS base
LABEL org.opencontainers.image.authors="Trifork"

# latest release available as of 2023/07/25
# IMPORTANT!! pyds versions are tightly coupled with 
# - the deepstream version
# - the python version
# - the OS version
ARG PYDS_VERSION=1.1.6

# latest release available as of 2023/07/25
# NOTE: Aravis v0.8.27 requires meson >= 0.57
ARG MESON_VERSION=1.2.0

# latest release available as of 2023/07/25
ARG ARAVIS_VERSION=0.8.27 

# we will need these variables to install from the requirements.txt
ARG GITHUB_USER
ARG GITHUB_TOKEN


RUN apt-get update && apt-get install -y \
    sudo git wget \
    python3 python3-pip python3.8-dev python3-gi python-gi-dev \
    python3-gst-1.0 python3-gi-cairo \
    gstreamer1.0-python3-plugin-loader libgirepository1.0-dev gobject-introspection \
    libcanberra-gtk-module libcanberra-gtk3-module

RUN python3 -m pip install --upgrade pip wheel


# Install the python bindings
RUN mkdir /dependencies && \
    wget --content-disposition https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v${PYDS_VERSION}/pyds-${PYDS_VERSION}-py3-none-linux_x86_64.whl -P /dependencies
RUN pip3 install /dependencies/pyds-${PYDS_VERSION}-py3-none-linux_x86_64.whl


# install dependencies

## fix: clean previous version of pyyaml
RUN rm -rf /usr/lib/python3/dist-packages/PyYAML-5.3.1.egg-info /usr/local/lib/python3.8/dist-packages/PyYAML-5.3.1.dist-info/

## fix: remove previous version of meson
RUN apt-get -y remove meson && \
    apt-get -y autoremove

COPY ./requirements.txt /dependencies/requirements.txt
RUN python3 -m pip install --upgrade -r /dependencies/requirements.txt

# install latest meson
RUN wget --content-disposition https://github.com/mesonbuild/meson/releases/download/${MESON_VERSION}/meson-${MESON_VERSION}.tar.gz -P /dependencies && \
    cd /dependencies && \
    tar xzvf meson-${MESON_VERSION}.tar.gz && \
    rm meson-${MESON_VERSION}.tar.gz

# install aravis dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev libglib2.0-dev cmake libusb-1.0-0-dev gobject-introspection \
    libgtk-3-dev gtk-doc-tools  xsltproc libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
    libgirepository1.0-dev gettext 


# Download and install Aravis, 
RUN wget https://github.com/AravisProject/aravis/releases/download/${ARAVIS_VERSION}/aravis-${ARAVIS_VERSION}.tar.xz && \
    tar -xvf aravis-${ARAVIS_VERSION}.tar.xz && \
    cd aravis-${ARAVIS_VERSION} && \
    python3 /dependencies/meson-${MESON_VERSION}/meson.py build && \
    cd build && \
    ninja && \
    ninja install

# install additional gstreamer plugins
RUN sh /opt/nvidia/deepstream/deepstream/user_additional_install.sh
