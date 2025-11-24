import io
import socket
import Adafruit_PCA9685
import threading
import json
import time



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
pwm_right = 0
pwm_back = 2

##### LOAD CONFIG ##################
with open('/home/pi/SERVER/diag/fathom_config.json') as data_file:
    config = json.load(data_file)
    pwm_left = config["pwm_left"]
    pwm_right = config["pwm_right"]
    pwm_back = config["pwm_back"]

def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)

def setupLock():
    global scale_lock, pitch_lock
    scale_lock = threading.Lock()
    pitch_lock = threading.Lock()


def send_val_to_escs(val):

    pwm.set_pwm(pwm_right,0,int(val))
    pwm.set_pwm(pwm_left,0,int(val))
    pwm.set_pwm(pwm_back, 0, int(val))

setupPWM()
setupLock()

print("Begin esc calibration")
send_val_to_escs(0)
time.sleep(4)
send_val_to_escs(600)
time.sleep(1)
send_val_to_escs(150)
time.sleep(1)
send_val_to_escs(375)
print("Calibrated escs")

