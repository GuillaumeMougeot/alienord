FROM python:3.8.10

RUN pip3 install --upgrade pip wheel

COPY ./requirements.txt /dependencies/requirements.txt
RUN python3 -m pip install --upgrade -r /dependencies/requirements.txt

COPY ./app /workspaces/gps/app
COPY ./configs /workspaces/gps/configs
COPY ./schemas /workspaces/gps/schemas
COPY ./utils /workspaces/gps/utils

WORKDIR /workspaces/gps

CMD ["python3", "-m", "app.update_gps"]