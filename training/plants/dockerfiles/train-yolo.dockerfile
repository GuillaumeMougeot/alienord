FROM python:3.8.10


RUN apt-get update && apt-get install -y sudo libgl1 ffmpeg && \
    python3 -m pip install --upgrade pip wheel

ARG GITHUB_TOKEN
ARG GITHUB_USER
ARG USERNAME=trainer
ARG COMMIT_SHA=000bcd676d48eb236076aed111ab23ff0105de3d


RUN useradd --create-home --home /workspaces --shell /bin/bash "${USERNAME}" && \
    echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

WORKDIR /workspaces

USER ${USERNAME}

RUN mkdir -p dependencies && \
    mkdir -p .darwin/datasets

ENV VIRTUAL_ENV=/usr/local
ADD --chmod=655 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh 

COPY requirements-yolo.txt dependencies/requirements.txt

USER root
RUN /workspaces/.cargo/bin/uv pip install --no-cache -r dependencies/requirements.txt
USER ${USERNAME}

# install Deepstream YOLO to support newer YOLO versions (tested on v8)
RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo dependencies/DeepStream-Yolo && \
    cd dependencies/DeepStream-Yolo && \
    git checkout ${COMMIT_SHA} && \
    cp utils/export_yoloV8.py /workspaces

COPY scripts/setup_devcontainer.sh setup_devcontainer.sh

ENTRYPOINT [ "/bin/bash", "/workspaces/setup_devcontainer.sh" ]
