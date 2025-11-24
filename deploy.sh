#!/bin/sh

DRONE_IP=$1

# make server directory
ssh pi@${DRONE_IP} "mkdir SERVER"
#send scripts to drone
scp -r ./* "pi@${DRONE_IP}:SERVER/"

# only run setup once
#ssh pi@${DRONE_IP} "/home/pi/SERVER/setup.sh"

