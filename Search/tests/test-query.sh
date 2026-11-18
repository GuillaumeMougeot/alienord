#!/bin/bash

if [ $# -eq 1 ]; then
    url="$1"
elif [ $# -eq 0 ]; then
    url="localhost:8080"
else
    echo "Usage: $0 <OPTIONAL[url]>" 
    exit 1
fi

curl https://http-query-7pjwfliw5q-ew.a.run.app \
  -X POST \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer add88dee-5da8-4ed9-bd1e-2c739c39e372" \
  -d '{
        "min_tp": "20230101T131053.513",
        "max_tp": "20230805T131053.513",
        "device": ["xnx1", "xnx2"],
        "country": ["Denmark"],
        "plant_type": ["lupin", "golden"]
      }'