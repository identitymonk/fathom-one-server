import io
import socket
import Adafruit_PCA9685
import threading

import json
import time
from fathom_calibrator import Calibrator
from fathom_accelerometer import Accelerometer

#import RPi.GPIO as GPIO

#GPIO.setmode(GPIO.BCM)            # choose BCM or BOARD
#GPIO.setup(20, GPIO.OUT) # set a port/pin as an output
#GPIO.output(20, 1)

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
pwm_left = 1
pwm_right = 2
pwm_back = 0
###################################################
#### STREAMING CONSTANTS ####
MCAST_GRP="192.168.0.101"
MCAST_PORT = 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8002))
#server_socket.listen(5)


CALIBRATION_FILE = 'calibration'
calibrator = Calibrator(CALIBRATION_FILE)
accelerometer = Accelerometer(CALIBRATION_FILE,calibrator.getIMU())
should_hold_pitch = False
PH = None

##### LOAD CONFIG ##################
with open('diag/fathom_config.json') as data_file:
    config = json.load(data_file)
    pwm_left = config["pwm_left"]
    pwm_right = config["pwm_right"]
    pwm_back = config["pwm_back"]



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
            current_roll = accelerometer.get_roll()

            # if roll is too extreme, do not pitch hold
            if -30 < current_roll < 30:
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


def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)
    #time.sleep(2);
    #send_thrust_to_esc(375,1,1)
    #send_thrust_to_pitch(375)

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

            # Check if thrust is currently neutral and scale is not zero
            # If so, go into zero point turn mode
            if thrust == servo_neutral and (left_scale < 1 or right_scale < 1):
                thrust = 395
                print("PANNING")


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

        pwm.set_pwm(pwm_right,0,int(right_thrust))
        pwm.set_pwm(pwm_left,0,int(left_thrust))
        #print("SENDING THRUST: ")
        #print(thrust)
        #print(left_thrust)
        #print(right_thrust)

def send_thrust_to_esc_from_externalController(val,left_scale,right_scale):
    global scale_lock,thruster_scale_left,thruster_scale_right,thrust
    global servo_min,servo_max,servo_neutral


    with scale_lock:
        left_thrust = None
        right_thrust = None

        thruster_scale_left = left_scale
        thruster_scale_right = right_scale

        # Check if thrust is currently neutral and scale is not zero
        # If so, go into zero point turn mode
        if thrust == servo_neutral and (left_scale < 1 or right_scale < 1):
            thrust = 395
            print("PANNING")

        else:
            thrust = val

        if thrust > servo_neutral:
            thrust_diff = thrust - servo_neutral
            left_thrust = servo_neutral + (thruster_scale_left * thrust_diff)
            right_thrust = servo_neutral + (thruster_scale_right * thrust_diff)
        else:
            thrust_diff = servo_neutral - thrust
            left_thrust = servo_neutral - (thruster_scale_left * thrust_diff)
            right_thrust = servo_neutral - (thruster_scale_right * thrust_diff)

        pwm.set_pwm(pwm_right,0,int(right_thrust))
        pwm.set_pwm(pwm_left,0,int(left_thrust))


def send_thrust_to_pitch(val):
    global pitch,pwm_back,pwm
    #with pitch_lock:
    if (val < 375) and (pitch > 375):
        pwm.set_pwm(pwm_back, 0, int(servo_neutral))
    pitch = val

    pwm.set_pwm(pwm_back,0,int(val))
    #print("SENDING PITCH: ")
    #print(val)

def drag_correct(pitch_val):
    global accelerometer, pwm
    # check roll
    current_roll = accelerometer.get_roll()


    # if roll is too extreme, do not pitch hold
    if -30 < current_roll < 30:
        # if pitch is up, throttle negative
        pwm.set_pwm(pwm_back, 0, pitch_val)



def pitch_hold():
    global should_hold_pitch,pitch_lock
    with pitch_lock:
        should_hold_pitch = True
    while True:
        with pitch_lock:
            if should_hold_pitch:
                # check pitch
                current_pitch = accelerometer.get_pitch()
                #print(current_pitch)
                # if pitch is up, throttle negative
                if current_pitch > 30:
                    send_thrust_to_pitch(320)
                    #print("pitched up")
                elif current_pitch > 15:
                    send_thrust_to_pitch(340)
                    #print("pitched up")
                # if pitch is down, throttle positive
                elif current_pitch < -5:
                    send_thrust_to_pitch(405)
                    #print("pitched down")
                elif current_pitch < -30:
                    send_thrust_to_pitch(420)
                    #print("pitched down")
                #else:
                    #print("Level")
                time.sleep(1)
            else:
                #print("breaking")
                break

def stop_pitch_hold():
    global should_hold_pitch,PH
    if PH.isAlive():
        PH.stop()
        PH.join()



setupLock()
setupPWM()

while True:

    should_hold_pitch = False
    PH = PitchHold()
    while True:
       data, addr = server_socket.recvfrom(1024) # buffer size is 1024 bytes
       data_elements = data.split(",")
       tag = data_elements[0]
       #print(data)

       if tag == "PITCH_HOLD":
           t = int(float(data_elements[1]))

           # mode 1
           #PH = PitchHold()
           #PH.start()

           # mode 2
           drag_correct(t)

       elif tag == "PITCH":
           #stop_pitch_hold()
           t = int(float(data_elements[1]))
           send_thrust_to_pitch(t)

       elif tag == "EXTERNAL":
           t = int(float(data_elements[1]))
           l = float(data_elements[2])
           r = float(data_elements[3])
           p = float(data_elements[4])
           send_thrust_to_esc_from_externalController(t, l, r)
           send_thrust_to_pitch(p)


       else:
           t = int(float(data_elements[1]))
           l = float(data_elements[2])
           r = float(data_elements[3])
           send_thrust_to_esc(t,l,r)


       #print "received message:", data_elements
server_socket.close()
