import io
import socket
import Adafruit_PCA9685
import threading
from fathom_accelerometer import Accelerometer
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
current_pitch = 375
scale_lock = None
pitch_lock = None
# outputs
pwm_left = 9
pwm_right = 8
pwm_back = 10

###################################################

CALIBRATION_FILE = 'calibration'
accelerometer = Accelerometer(CALIBRATION_FILE)

def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()

def setupLock():
    global scale_lock, pitch_lock
    scale_lock = threading.Lock()
    pitch_lock = threading.Lock()

def send_thrust_to_pitch(val):
    global pitch,pwm_back,pwm
    #with pitch_lock:
    if (val < 375) and (pitch > 375):
        pwm.set_pwm(pwm_back, 0, int(servo_neutral))
    pitch = val

    pwm.set_pwm(pwm_back,0,int(val))
    print("SENDING PITCH: ")
    print(val)

setupPWM()
setupLock()

# Send pitch 400 until level
send_thrust_to_pitch(400);

while True:
    #check pitch
    current_pitch = accelerometer.get_pitch()
    print(current_pitch)
    #if pitch is up, throttle negative
    if current_pitch > 5:
        send_thrust_to_pitch(300)
        print("pitched up")
    #if pitch is down, throttle positive
    elif current_pitch < -5:
        send_thrust_to_pitch(420)
        print("pitched down")
    else:
        print("Level")
    time.sleep(1)



