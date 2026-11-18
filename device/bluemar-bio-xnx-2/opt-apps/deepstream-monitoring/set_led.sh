#!/bin/bash

# Arguments
# $1 = led_id: ID of the led to be used
# $2 = on | off

## this should run on the host, not inside the container

./se70_tool doled $1 $2

