import io
import socket
import Adafruit_PCA9685
import threading




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
    while True:
        # send_thrust_to_pitch(servo_max);
        # send_thrust_to_esc(servo_max,0,1);
        input = raw_input("Thruster value (ex: L425):")
        thruster = input[0:1]
        val = input[1:5]

        if (thruster.upper() == "L"):
            send_thrust_to_esc(val, 1, 0);
            print("Left:" + val);
        if (thruster.upper() == "R"):
            # blah
            send_thrust_to_esc(val, 0, 1);
            print("Right:" + val);
        if (thruster.upper() == "T"):
            send_thrust_to_pitch(val)
            print("Tail:" + val);
        if (thruster.upper() == "A"):
            # send to all
            send_thrust_to_esc(val, 1, 1);
            send_thrust_to_pitch(val)
        if (thruster.upper() == "S"):
            # send to all
            send_thrust_to_esc(val, 1, 1);
            print("All:" + val);
        if (thruster.upper() == "N"):
            # send neutral to all
            send_thrust_to_esc(375, 1, 1);
            send_thrust_to_pitch(val)
            print("Neutral.");


