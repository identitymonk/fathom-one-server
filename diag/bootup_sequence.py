import io
import socket
import Adafruit_PCA9685
import threading
import json
from subprocess import call
import time



import RPi.GPIO as GPIO
from subprocess import call


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
pwm_lights = 3
shield_pin = 19



##### LOAD CONFIG ##################
with open('/home/pi/SERVER/diag/fathom_config.json') as data_file:
    config = json.load(data_file)
    pwm_left = config["pwm_left"]
    pwm_right = config["pwm_right"]
    pwm_back = config["pwm_back"]
    shield_pin = config["shield_pin"]

GPIO.setmode(GPIO.BCM)            # choose BCM or BOARD
GPIO.setup(shield_pin, GPIO.OUT) # set a port/pin as an output
GPIO.output(shield_pin, 1)

### TURN OFF WIFI
#call("sudo ifconfig wlan0 down", shell=True)


def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)



def send_val_to_lights(val):

    pwm.set_pwm(pwm_lights,0,int(val))


setupPWM()


print("Begin bootup sequence")
i = 0
while i < 9:
    send_val_to_lights(0)
    time.sleep(.25)
    send_val_to_lights(25)
    time.sleep(.1)
    send_val_to_lights(50)
    time.sleep(.1)
    send_val_to_lights(75)
    time.sleep(.1)
    send_val_to_lights(100)
    time.sleep(.1)
    send_val_to_lights(125)
    time.sleep(.1)
    send_val_to_lights(150)
    time.sleep(.1)
    send_val_to_lights(175)
    time.sleep(.1)
    send_val_to_lights(200)
    time.sleep(.1)
    send_val_to_lights(225)
    time.sleep(.1)
    send_val_to_lights(250)
    time.sleep(.1)
    send_val_to_lights(275)
    time.sleep(.1)
    send_val_to_lights(300)
    time.sleep(.1)
    send_val_to_lights(325)
    time.sleep(.1)
    send_val_to_lights(350)
    time.sleep(.1)
    send_val_to_lights(375)
    time.sleep(.1)
    send_val_to_lights(400)
    time.sleep(.1)
    send_val_to_lights(425)
    time.sleep(.1)
    send_val_to_lights(450)
    time.sleep(.1)
    send_val_to_lights(475)
    time.sleep(.1)
    send_val_to_lights(500)
    time.sleep(.1)
    send_val_to_lights(525)
    time.sleep(.1)
    send_val_to_lights(550)
    time.sleep(.1)
    send_val_to_lights(600)
    time.sleep(.2)

    send_val_to_lights(575)
    time.sleep(.1)
    send_val_to_lights(550)
    time.sleep(.1)
    send_val_to_lights(525)
    time.sleep(.1)
    send_val_to_lights(500)
    time.sleep(.1)
    send_val_to_lights(475)
    time.sleep(.1)
    send_val_to_lights(450)
    time.sleep(.1)
    send_val_to_lights(425)
    time.sleep(.1)
    send_val_to_lights(400)
    time.sleep(.1)
    send_val_to_lights(375)
    time.sleep(.1)
    send_val_to_lights(350)
    time.sleep(.1)
    send_val_to_lights(325)
    time.sleep(.1)
    send_val_to_lights(300)
    time.sleep(.1)
    send_val_to_lights(275)
    time.sleep(.1)
    send_val_to_lights(250)
    time.sleep(.1)
    send_val_to_lights(225)
    time.sleep(.1)
    send_val_to_lights(200)
    time.sleep(.1)
    send_val_to_lights(175)
    time.sleep(.1)
    send_val_to_lights(150)
    time.sleep(.1)
    send_val_to_lights(125)
    time.sleep(.1)
    send_val_to_lights(100)
    time.sleep(.1)
    send_val_to_lights(75)
    time.sleep(.1)
    send_val_to_lights(50)
    time.sleep(.1)
    send_val_to_lights(25)
    time.sleep(.1)
    send_val_to_lights(0)

    time.sleep(1)
    i = i + 1

    if i == 8:
        call("python /home/pi/SERVER/diag/calibrate_esc.py", shell=True)

print("End bootup sequence")

