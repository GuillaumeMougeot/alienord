# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

####################################################################
# YOLO DEPENDENCIES STAGE
####################################################################

FROM nvcr.io/nvidia/deepstream-l4t:6.2-triton as dependencies

# default commit is the latest for DeepStream-Yolo onnx export
# to use cfg+wts old export use this commit instead: ab6de54c4398c1daeb6fc31b06af29f97663f211
ARG COMMIT_SHA=b738644f6e5c8918e9035647209af3814e406c17

RUN apt-get install -y build-essential && \
    /opt/nvidia/deepstream/deepstream/user_additional_install.sh && \
    apt-get install -y libnvinfer-dev 

# install Deepstream YOLO to support newer YOLO versions (tested on v8)
RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo /dependencies/DeepStream-Yolo && \
    cd /dependencies/DeepStream-Yolo && \
    git checkout ${COMMIT_SHA} && \
    CUDA_VER=11.4 make -C nvdsinfer_custom_impl_Yolo


####################################################################
# BASE STAGE
####################################################################

FROM nvcr.io/nvidia/deepstream-l4t:6.2-base AS base
LABEL org.opencontainers.image.authors="Trifork"

RUN apt-get update && apt-get install -y \
    pkg-config wget gettext vim \
    python3 python3-pip python3.8-dev python3-gi python-gi-dev \
    python3-gst-1.0 python3-gi-cairo \
    gstreamer1.0-python3-plugin-loader libgirepository1.0-dev gobject-introspection

RUN pip3 install --upgrade pip wheel

# install pyds
RUN mkdir /dependencies && \
    wget --content-disposition https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.6/pyds-1.1.6-py3-none-linux_aarch64.whl -P /dependencies && \
    python3 -m pip install /dependencies/*.whl

## fix: clean previous version of pyyaml
RUN rm -rf /usr/lib/python3/dist-packages/PyYAML-5.3.1.egg-info /usr/local/lib/python3.8/dist-packages/PyYAML-5.3.1.dist-info/

COPY ./requirements.txt /dependencies/requirements.txt
COPY ./models/models-lock.json /workspaces/vd-biodiversity/bio/models/models-lock.json

####################################################################
# BUILDER STAGE
####################################################################

FROM base as builder

# install requirements.txt
COPY ./secrets/.env /workspaces/vd-biodiversity/secrets/.env
RUN export $(cat /workspaces/vd-biodiversity/secrets/.env | xargs) && \
    python3 -m pip install --upgrade -r /dependencies/requirements.txt

# Pull models
COPY ./secrets/nordfou-biodiversity-2cd0fb3af162.json /workspaces/vd-biodiversity/secrets/nordfou-biodiversity-2cd0fb3af162.json
COPY ./utils /workspaces/vd-biodiversity/bio/utils
WORKDIR /workspaces/vd-biodiversity/bio
RUN python3 -m utils.pull_models

####################################################################
# RELEASE STAGE
####################################################################

FROM base as release

# Copy yolo dependencies
COPY --from=dependencies /dependencies/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so /opt/nvidia/deepstream/deepstream/lib/

# Copy python dependencies
COPY --from=builder /usr/local/lib/python3.8/dist-packages /usr/local/lib/python3.8/dist-packages

# Copy the needed code for the app to work
COPY --from=builder /workspaces/vd-biodiversity/bio/models /workspaces/vd-biodiversity/bio/models
COPY ./adapters /workspaces/vd-biodiversity/bio/adapters
COPY ./app /workspaces/vd-biodiversity/bio/app
COPY ./configs /workspaces/vd-biodiversity/bio/configs
COPY ./schemas /workspaces/vd-biodiversity/bio/schemas
COPY ./utils /workspaces/vd-biodiversity/bio/utils


# install aravis dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev libglib2.0-dev cmake libusb-1.0-0-dev gobject-introspection \
    libgtk-3-dev gtk-doc-tools  xsltproc libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
    libgirepository1.0-dev gettext

# install meson and ninja
RUN pip3 install --upgrade meson ninja

# Download and install Aravis, latest release available as of 2023/04/27
RUN wget https://github.com/AravisProject/aravis/releases/download/0.8.26/aravis-0.8.26.tar.xz && \
    tar -xvf aravis-0.8.26.tar.xz && \
    cd aravis-0.8.26 && \
    meson build && \
    cd build && \
    ninja && \
    ninja install

# install tao-converter
RUN wget --content-disposition 'https://api.ngc.nvidia.com/v2/resources/nvidia/tao/tao-converter/versions/v3.22.05_trt8.4_aarch64/files/tao-converter' -O /usr/local/bin/tao-converter && \
    chmod +x /usr/local/bin/tao-converter 

RUN sh /opt/nvidia/deepstream/deepstream/install.sh ; \
    sh /opt/nvidia/deepstream/deepstream/user_additional_install.sh

WORKDIR /workspaces/vd-biodiversity/bio

CMD /bin/bash -c "umask 0002 && python3 -m app.main"