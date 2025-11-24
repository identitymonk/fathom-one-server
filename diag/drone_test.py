from subprocess import call
import RPi.GPIO as GPIO
from fathom_calibrator import Calibrator
from fathom_depth_sensor import DepthSensor
from fathom_magnetometer import Magnetometer

import io
import json
import socket
from subprocess import Popen, PIPE
from time import sleep

import Adafruit_PCA9685
import threading

##### LOAD CONFIG ##################
with open('fathom_config.json') as data_file:
    config = json.load(data_file)

####### DEPTH ############
depthSensor = DepthSensor()
##########################

########### CALIBRATION #############
CALIBRATION_FILE = 'calibration'
calibrator = Calibrator(CALIBRATION_FILE)
magnetometer = Magnetometer(CALIBRATION_FILE,calibrator.getIMU())
#accelerometer = Accelerometer(CALIBRATION_FILE,calibrator.getIMU())
#####################################

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
pwm_left = config["pwm_left"]
pwm_right = config["pwm_right"]
pwm_back = config["pwm_back"]

###### SHIELD #######
shield_pin = config["shield_pin"]
GPIO.setmode(GPIO.BCM)            # choose BCM or BOARD
GPIO.setup(shield_pin, GPIO.OUT) # set a port/pin as an output
GPIO.output(shield_pin, 1)



###### LIGHTS ##########
pwm_lights = 3

def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)

def setupLock():
    global scale_lock, pitch_lock
    scale_lock = threading.Lock()
    pitch_lock = threading.Lock()


def printHeader(header):
    print("##########################")
    print(str(header))
    print("##########################")



printHeader("Beginning OS check....")
status_raspbian = False
raspbian_command = "uname"
p = Popen([raspbian_command, "-a"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
out, err = p.communicate()
if "4.4.50" in out:
    status_raspbian = True

# check python version
status_python = False
python_command = "python"
p = Popen([python_command, "--version"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
out, err = p.communicate()

if "2.7.9" in out:
    status_python = True


# check rc local
status_rclocal = False
rclocal_command = "cat"
p = Popen([rclocal_command, "/etc/rc.local"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
out, err = p.communicate()

if "gpio" in out or "app.sh" in out:
    status_rclocal = True


print("Raspbian version:" + str(status_raspbian))
print("Python version:" + str(status_python))
print("rc.local version:" + str(status_rclocal))


#exit(1);




print("Setting up pwm...")
setupPWM()
setupLock()
sleep(1)
printHeader("Bootup sequence check...")
status_bootup_headlight = raw_input("Did the headlights flash during bootup? (y/n)")
status_bootup_esc = raw_input("Did the drone's ESC's calibrate during boot up? (y/n)")


sleep(1)

### CHECK HEADLIGHTS ####
printHeader("Beginning headlight check...")
pwm.set_pwm(pwm_lights,0,int(600))
status_headlight_now = raw_input("Are the headlights on now? (y/n)")
sleep(2)
pwm.set_pwm(pwm_lights,0,int(0))
status_headlights_off = raw_input("Headlights off now? (y/n)")


#### CHECK VOLTAGE ####
printHeader("Beginning voltage check...")
raw_input("Enter the voltage reading from each cell of the battery. This will require the user to place the drone on the multimultimultimeter and read each cell voltage. Script will verify that the battery cells are within a specified range and that they are all the same, +- 0.01V. Press enter when you are ready to proceed")
status_voltage_one = raw_input("Cell one voltage:")
status_voltage_two = raw_input("Cell two voltage:")
status_voltage_three = raw_input("Cell three voltage:")



#### CHECK MOTORS ####
printHeader("Beginning motor check...")
status_motors_connected = raw_input("Motors connected? (y/n)")
status_motors_clear = raw_input("Are your hands and any obstructions removed from the motors? (y/n) ")
print("Checking right motor...")
sleep(1)
pwm.set_pwm(pwm_right,0,int(450))
status_motors_right_forward = raw_input("Did the motor run forward as expected? (y/n) ")
pwm.set_pwm(pwm_right,0,int(375))
sleep(2)
pwm.set_pwm(pwm_right,0,int(300))
status_motors_right_reverse = raw_input("Did the motor run backward as expected? (y/n) ")
pwm.set_pwm(pwm_right,0,int(375))
sleep(2)

print("Checking left motor...")
sleep(1)
pwm.set_pwm(pwm_left,0,int(450))
status_motors_left_forward = raw_input("Did the motor run forward as expected? (y/n) ")
pwm.set_pwm(pwm_left,0,int(375))
sleep(2)
pwm.set_pwm(pwm_left,0,int(300))
status_motors_left_reverse = raw_input("Did the motor run backward as expected? (y/n) ")
pwm.set_pwm(pwm_left,0,int(375))
sleep(2)

print("Checking tail motor...")
sleep(1)
pwm.set_pwm(pwm_back,0,int(450))
status_motors_tail_forward = raw_input("Did the motor run forward as expected? (y/n) ")
pwm.set_pwm(pwm_back,0,int(375))
sleep(2)
pwm.set_pwm(pwm_back,0,int(300))
status_motors_tail_reverse = raw_input("Did the motor run backward as expected? (y/n) ")
pwm.set_pwm(pwm_back,0,int(375))
sleep(2)

print("End motor check.")
print("##########################")
sleep(2)

### CAMERA ####
printHeader("Beginning camera check...")
sleep(3)
raw_input("Press enter when you are ready to check the camera?")
camera_command = "raspivid -t 5000"
call(camera_command, shell=True)
sleep(5)
status_camera_on = raw_input("Were you able to see the camera feed? (y/n)")
status_camera_clear = raw_input("Is the feed visible and clear? (y/n)")
print("End camera check.")
print("##########################")
sleep(2)

### THERMISTOR ###
printHeader("Calibrating thermistor... ")
print("End thermistor...")
sleep(2)

### AUX SENSORS ####
printHeader("Beginning aux sensor check...")
# Look for input
heading = magnetometer.get_heading()
depth = depthSensor.read_depth()
#print("Heading: "+str(heading))
try:
    float(heading)
    status_heading = True
    print("Successfully reading data from IMU")
except ValueError:
    status_heading = False
    print("ERROR: Unable to read data from IMU")

# zero depth
depthSensor.calibrate()
print("End aux sensor check...")


### COMPASS ####
printHeader("Checking compass...")
raw_input("Press enter when you are ready to calibrate the compass. Calibration will run for 20 seconds.")
calibrator.calibrate_magnetometer(duration=20,interval=.1)
sleep(20)
heading = magnetometer.get_heading()
print("Done with calibration. Current heading: "+heading)
status_heading_accurate = raw_input("Is current heading accurate? (y/n)")
print("Done checking compass...")
sleep(1)


printHeader("CHECK COMPLETE")
print("The drone check is complete.")
status_notes = raw_input("Any other notes you would like to add? Please type them now:")
status_technician = raw_input("Please enter your initials:")


