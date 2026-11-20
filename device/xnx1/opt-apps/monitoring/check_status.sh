#!/bin/bash

# Check parameters
if [ $# -ne 1 ]; then
    echo "Usage: $0 <app>"
    exit 1
fi

app="$1"

status=$(systemctl show -p SubState --value "$app")

if [ "$status" == "exited" ]; then
    exit_status=$(systemctl show -p ExecMainStatus --value "$app")
    if [ "$exit_status"=="0" ]; then
        echo "Status: EXITED"
    else
        echo "Status: ERROR"
    fi
else
    if [ "$status" == "running" ] || [ "$status" == "waiting" ]; then
        echo "Status: MISSING"
    else
        echo "Status: ERROR"
    fi
fi
