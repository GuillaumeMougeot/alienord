FROM python:3.8.10


RUN apt-get update && apt-get install -y sudo libgl1 ffmpeg && \
    python3 -m pip install --upgrade pip wheel

ARG GITHUB_TOKEN
ARG GITHUB_USER
ARG USERNAME=distiller

RUN useradd --create-home --home /workspaces --shell /bin/bash "${USERNAME}" && \
    echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

WORKDIR /workspaces

USER ${USERNAME}

# create directories
RUN mkdir -p dependencies && \
    mkdir -p .darwin/datasets

# autodistill will also install python packages when importing dependencies
# that's why we want to install the requirements in the user space, instead of root
COPY requirements-autodistill.txt dependencies/requirements.txt
RUN python3 -m pip install -r dependencies/requirements.txt

COPY scripts/setup_devcontainer.sh setup_devcontainer.sh

ENTRYPOINT [ "/bin/bash", "/workspaces/setup_devcontainer.sh" ]