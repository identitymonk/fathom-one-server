#!/bin/sh

#gpio -g mode 2 alt0
#sleep 60

python diag/bootup_sequence.py &

###############################
################################
### START CAMERA STREAMER ######
sudo python server/fathom_camera.py &

################################
################################
### START REST API      ########
sudo python server/fathom_server.py -debug &

###############################

#sleep 10

#python diag/calibrate_esc.py


sleep 35
################################
### START UDP RECEIVERS ########
#python server/fathom_controls.py &
python server/fathom_thruster.py &
python server/fathom_telemetry_server.py &
