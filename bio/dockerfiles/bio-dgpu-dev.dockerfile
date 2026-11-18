FROM bio-dgpu:base

# this user exists already in the base image
ARG USERNAME=devel

# default commit is the latest for DeepStream-Yolo onnx export
# to use cfg+wts old export use this commit instead: ab6de54c4398c1daeb6fc31b06af29f97663f211
ARG COMMIT_SHA=b738644f6e5c8918e9035647209af3814e406c17

# install Deepstream YOLO to support newer YOLO versions (tested on v8)
RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo /dependencies/DeepStream-Yolo && \
    cd /dependencies/DeepStream-Yolo && \
    git checkout ${COMMIT_SHA} && \
    CUDA_VER=11.8 make -C nvdsinfer_custom_impl_Yolo && \
    cp nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so /opt/nvidia/deepstream/deepstream/lib/

# create a user 
RUN useradd --create-home --home /workspaces --shell /bin/bash "${USERNAME}" && \
    echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

RUN usermod -a -G audio ${USERNAME}

# set user from now on
USER ${USERNAME}