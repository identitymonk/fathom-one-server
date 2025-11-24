#!/bin/bash
DRONE_IP=$1
#ssh pi@{DRONE_IP}

while true
do
    python battery_check.py
	sleep 5
done
