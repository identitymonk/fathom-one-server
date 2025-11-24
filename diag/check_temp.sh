#!/bin/bash
DRONE_IP=$1
#ssh pi@{DRONE_IP}

while true
do
    vcgencmd measure_temp
    python thermister.py
	sleep 1
done
