#!/bin/bash

if [[ -z "$DEEPSTREAM_PID_PATH" ]]; then
    echo "Must provide DEEPSTREAM_PID_PATH in environment" 1>&2
    exit 1
fi

find_app_pid() {
    # the app should provide its pid 
    # ---inside the docker container--- 
    # through this pid file
    cat $DEEPSTREAM_PID_PATH
}

get_digital_input() {
    # sleep 30 && echo "DI 1: low" # This line is used for testing only, it should be commented out otherwise
    ./se70_tool getdi 1
}

kill_pid() {
    ## call it with the pid of the app inside the docker container
    container_id=$(docker ps -a | grep deepstream_app | awk '{print $1}')
    docker exec $container_id bash -c "kill -s SIGUSR1 $1"
}


## This is not ideal, we should avoid active polling as it consumes CPU
## With 50ms sleep time it consumes 5% of CPU
while true; do
    
    di=$(get_digital_input)

    # send a signal to the app if the button was pressed
    if [[ "$di" == *low* ]]; then

        echo "Physical button was pressed to start recording!"

        pid=$(find_app_pid)
        kill_pid $pid

        # debounce
        sleep 5

    fi

    sleep 0.05
    
done