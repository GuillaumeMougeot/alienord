#!/bin/bash

## setup darwin authenticated account

DARWIN_SECRET=/workspaces/secrets/darwin.env

if [ ! -f "$DARWIN_SECRET" ]; then
  echo "Darwin secret not found!" && exit 1
fi

source "$DARWIN_SECRET"

if [ -z "$DARWIN_API_KEY" ]; then
  echo "DARWIN_API_KEY is not defined inside darwin secret!" && exit 1
fi

cat > ~/.darwin/config.yaml << EOF
global:
  api_endpoint: https://darwin.v7labs.com/api/
  base_url: https://darwin.v7labs.com
  default_team: triforkext
teams:
  triforkext:
    api_key: ${DARWIN_API_KEY}
    datasets_dir: /workspaces/.darwin/datasets
EOF


## devcontainer default command, needed to keep the container up and running
while sleep 1000; do :; done