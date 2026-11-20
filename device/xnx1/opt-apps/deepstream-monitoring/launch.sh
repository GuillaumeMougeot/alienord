#!/bin/bash

source .env

read_heartbeat(){
    cat $PATH_TO_HEARTBEAT
}

# A fresh heartbeat only proves the app started: it is written once per start, so an app
# that crash-loops every ~30 s keeps it fresh. Also require that the container's latest
# frame-rate report (nvdslogger, every 5 s) is recent and non-zero for every camera.
# Read only the end of the container log and check the report's age here: "docker logs --since"
# scans the whole file from the start, which takes ~30 s on a large log and finds nothing
# once a power cut has left damaged lines in it.
frames_flowing(){
    perf=$(timeout 10 docker logs --timestamps --tail 50 deepstream_app 2>&1 | grep "PERF" | tail -1)
    if [ -z "$perf" ]; then
        echo "No frame rate reported"
        return 1
    fi
    reported=$(date -d "${perf%% *}" +%s 2>/dev/null) || { echo "Unreadable frame rate report"; return 1; }
    age=$(( $(date +%s) - reported ))
    if [ $age -gt $HEARTBEAT_SECONDS ]; then
        echo "Last frame rate report is $age s old"
        return 1
    fi
    fps=$(echo "$perf" | grep -oE 'FPS_[0-9]+ \([0-9.]+\)')
    echo "Frame rate: $(echo $fps)"
    # match zero as text: awk would parse "0.20" as 0 under this system's comma-decimal locale
    [ -n "$fps" ] && ! echo "$fps" | sed -E 's/.*\(([0-9.]+)\)/\1/' | grep -qxE '0+(\.0+)?'
}

check_heartbeat(){
    heartbeat=$(read_heartbeat)

    if [ $((now - heartbeat)) -ge $((HEARTBEAT_SECONDS * 1000)) ]; then
        echo "Heartbeat outdated, turning led ..."
        bash set_led.sh 1 on
    elif ! frames_flowing; then
        echo "No frames flowing, turning led ..."
        bash set_led.sh 1 on
    else
        echo "Heartbeat ok"
        bash set_led.sh 1 off
    fi
    
}

check_files_age(){
    for file in "$1"/*; do
        file_name=$(basename "$file")
        creation=$(date -d "$(stat -c %y "$file")" "+%s")
        if [ $((now - creation)) -lt $((DATA_DAYS * 24 * 3600)) ]; then
            echo "Timestamp for $file_name ok"
        else
            echo "Timestamp for $file_name is too old"
        fi
    done
}

check_annotations_imgs(){
    echo "Checking images"
    if [ "$(ls -A $PATH_TO_IMAGES)" ]; then
        check_files_age $PATH_TO_IMAGES
    else
        echo "There are no images to check"
    fi

    echo "Checking annotations"
    if [ "$(ls -A $PATH_TO_ANNOTATIONS)" ]; then
        check_files_age $PATH_TO_ANNOTATIONS
    else
        echo "There are no annotations to check"
    fi
}

while true; do

    now=$(date -u +%s%3N)

    echo "Checking heartbeat ..."
    
    if content=$(cat $PATH_TO_HEARTBEAT 2>/dev/null); then
        check_heartbeat
    else
        echo "Heartbeat is not available, turning led ..."
        bash set_led.sh 1 on
    fi

    if [ $((now - last_check)) -ge $((DATA_DAYS * 24 * 3600)) ]; then
        check_annotations_imgs
        last_check=$(date -u +%s%3N)
    fi

    sleep $HEARTBEAT_SECONDS
done
