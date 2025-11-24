import io
import socket
import threading

import time

pwm = None
############### PWM CONSTANTS #####################
# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096
servo_neutral = 375
thrust = 375
thruster_scale_left = 1
thruster_scale_right = 1
pitch = 375
scale_lock = None
pitch_lock = None
# outputs
pwm_left = 9
pwm_right = 8
pwm_back = 10
###################################################
#### STREAMING CONSTANTS ####
MCAST_GRP="192.168.0.101"
MCAST_PORT = 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8002))
#server_socket.listen(5)


CALIBRATION_FILE = 'calibration'
should_hold_pitch = False
PH = None



########### SETUP CAMERA THREAD ###
class PitchHold(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = False

    def run(self):
        print("IS STOPPED:"+str(self.stopped()))
        count = 0
        while not self._stop:
            print(self._stop)
            global accelerometer,pwm
            # check pitch
            #print("COUNT"+str(count))
            current_pitch = accelerometer.get_pitch()
            print(current_pitch)
            # if pitch is up, throttle negative
            if current_pitch > 5:
                pwm.set_pwm(pwm_back, 0, 300)
                #print("pitched up")
            # if pitch is down, throttle positive
            elif current_pitch < -5:
                pwm.set_pwm(pwm_back, 0, 420)
                #print("pitched down")
            #else:
                #print("Level")
            count = count+1
            time.sleep(1)

    def stop(self):
        self._stop = True

    def stopped(self):
        return self._stop

##################################

def setupLock():
    global scale_lock, pitch_lock
    scale_lock = threading.Lock()
    pitch_lock = threading.Lock()


def send_thrust_to_esc(val,left_scale,right_scale):
    global scale_lock,thruster_scale_left,thruster_scale_right,thrust
    global servo_min,servo_max,servo_neutral


    with scale_lock:
        left_thrust = None
        right_thrust = None
        # if thrust is 999999, then turning
        if val == 999999:
            #print("turning")
            thruster_scale_left = left_scale
            thruster_scale_right = right_scale

        else:
            thrust = val

        if thrust > servo_neutral:
            thrust_diff = thrust - servo_neutral
            left_thrust = servo_neutral + (thruster_scale_left * thrust_diff)
            right_thrust = servo_neutral + (thruster_scale_right * thrust_diff)
        else:
            #print("reverse")
            thrust_diff = servo_neutral - thrust
            left_thrust = servo_neutral - (thruster_scale_left * thrust_diff)
            right_thrust = servo_neutral - (thruster_scale_right * thrust_diff)

        # do something with the values

def send_thrust_to_pitch(val):
    global pitch,pwm_back,pwm
    #with pitch_lock:
    if (val < 375) and (pitch > 375):
        pwm.set_pwm(pwm_back, 0, int(servo_neutral))
    pitch = val

    # do something with the values



def pitch_hold():
    global should_hold_pitch,pitch_lock


def stop_pitch_hold():
    global should_hold_pitch,PH
    if PH.isAlive():
        PH.stop()
        PH.join()



setupLock()

while True:

    should_hold_pitch = False
    PH = PitchHold()
    while True:
       data, addr = server_socket.recvfrom(1024) # buffer size is 1024 bytes
       data_elements = data.split(",")
       tag = data_elements[0]

       if tag == "PITCH_HOLD":
           PH = PitchHold()
           #PH.start()
           #pwm.set_pwm(pwm_back,0,375)

       elif tag == "PITCH":
           #stop_pitch_hold()
           t = int(float(data_elements[1]))
           send_thrust_to_pitch(t)
       else:
           t = int(float(data_elements[1]))
           l = float(data_elements[2])
           r = float(data_elements[3])
           send_thrust_to_esc(t,l,r)


       #print "received message:", data_elements
server_socket.close()
