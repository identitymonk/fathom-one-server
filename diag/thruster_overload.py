import io
import socket
import Adafruit_PCA9685
import threading
import random


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


def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)

def setupLock():
    global scale_lock, pitch_lock
    scale_lock = threading.Lock()
    pitch_lock = threading.Lock()


def send_thrust_to_esc(val,left_scale,right_scale):
    global scale_lock,thruster_scale_left,thruster_scale_right,thrust
    global servo_min,servo_max,servo_neutral

    if(left_scale > 0):
        pwm.set_pwm(pwm_left, 0, int(val))
    if(right_scale > 0):
        pwm.set_pwm(pwm_right,0,int(val))


def send_thrust_to_pitch(val):
    global pitch
    with pitch_lock:
        pitch = val
        pwm.set_pwm(pwm_back,0,int(pitch))

setupPWM()
setupLock()

while True:
    offset = 405 + (random.randrange(0,50,2))
    send_thrust_to_pitch(offset)
    send_thrust_to_esc(offset+10,1,1)




