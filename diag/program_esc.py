import io
import socket
import Adafruit_PCA9685
import threading
from time import sleep




pwm = None
############### PWM CONSTANTS #####################
# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096
servo_neutral = 375
thrust = 375
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


def sendNext(channel):
    pwm.set_pwm(channel, 0, int(servo_min))
    sleep(3)
    pwm.set_pwm(channel, 0, int(servo_neutral))
    sleep(3)

def sendYes(channel):
    pwm.set_pwm(channel, 0, int(servo_max))
    sleep(3)
    pwm.set_pwm(channel, 0, int(servo_neutral))
    sleep(3)

def selectSetting(channel, setting):
    position = 1
    while position < setting:
        sendNext(channel)
        position = position + 1
    sendYes(channel)

def setIntoProgrammingMode(channel):
    pwm.set_pwm(channel, 0, int(servo_max))
    sleep(10)
    pwm.set_pwm(channel,0,int(servo_neutral))
    sleep(5)


setupPWM()

# 1 - 3
# 2 - ?
# 3 - 4
# 4 -
# 5 -
# 6 -
# 7 -
# 8 -

## Program left ESC
def programLeftESC():
    # 1 - Brake / reverse
    selectSetting(pwm_left,3)
    # 2 - Brake amount
    selectSetting(pwm_left,3)
    # 3 - Reverse amount
    selectSetting(pwm_left,4)
    # 4 - Punch control
    selectSetting(pwm_left,5)
    # 5 - Drag brake
    selectSetting(pwm_left,5)
    # 6 - Throttle dead band
    selectSetting(pwm_left,5)
    # 7 - Voltage cutoff
    selectSetting(pwm_left,2)
    # 8 - Motor timing
    selectSetting(pwm_left,2)




def programRightESC():
    # 1 - Brake / reverse
    selectSetting(pwm_right,3)
    # 2 - Brake amount
    selectSetting(pwm_right,3)
    # 3 - Reverse amount
    selectSetting(pwm_right,4)
    # 4 - Punch control
    selectSetting(pwm_right,5)
    # 5 - Drag brake
    selectSetting(pwm_right,5)
    # 6 - Throttle dead band
    selectSetting(pwm_right,5)
    # 7 - Voltage cutoff
    selectSetting(pwm_right,2)
    # 8 - Motor timing
    selectSetting(pwm_right,2)


def programBackESC():
    # 1 - Brake / reverse
    selectSetting(pwm_back,3)
    # 2 - Brake amount
    selectSetting(pwm_back,3)
    # 3 - Reverse amount
    selectSetting(pwm_back,4)
    # 4 - Punch control
    selectSetting(pwm_back,5)
    # 5 - Drag brake
    selectSetting(pwm_back,5)
    # 6 - Throttle dead band
    selectSetting(pwm_back,5)
    # 7 - Voltage cutoff
    selectSetting(pwm_back,2)
    # 8 - Motor timing
    selectSetting(pwm_back,2)

setIntoProgrammingMode(pwm_left)
programLeftESC()

sleep(5)
setIntoProgrammingMode(pwm_right)
programRightESC()

sleep(5)
setIntoProgrammingMode(pwm_back)
programBackESC()







