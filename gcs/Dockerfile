FROM python:3.8.10

RUN pip3 install --upgrade pip wheel

COPY ./requirements.txt /dependencies/requirements.txt
RUN python3 -m pip install --upgrade -r /dependencies/requirements.txt

COPY ./app /workspaces/gcs/app
COPY ./configs /workspaces/gcs/configs
COPY ./schemas /workspaces/gcs/schemas
COPY ./utils /workspaces/gcs/utils

WORKDIR /workspaces/gcs

CMD ["python3", "-m", "app.main"]