import csv
import json
import os
import requests
import subprocess
import sys
import threading
import time
import tinys3
import urllib2
from os import walk
from subprocess import call
import RPi.GPIO as GPIO
from flask import Flask, render_template
from flask import jsonify, request

from fathom_accelerometer import Accelerometer
from fathom_battery_monitor import BatteryMonitor

from fathom_calibrator import Calibrator
from fathom_depth_sensor import DepthSensor
from fathom_flight import Flight
from fathom_magnetometer import Magnetometer
from fathom_temperature_monitor import TemperatureMonitor

import update_server

import Adafruit_PCA9685


##### LOAD CONFIG ##################
with open('diag/fathom_config.json') as data_file:
    config = json.load(data_file)
####################################


######### SETUP CAMERA #############

cam = None
######################################

########### CALIBRATION #############
CALIBRATION_FILE = 'calibration'
calibrator = Calibrator(CALIBRATION_FILE)
magnetometer = Magnetometer(CALIBRATION_FILE,calibrator.getIMU())
accelerometer = Accelerometer(CALIBRATION_FILE,calibrator.getIMU())
#####################################

####### DEPTH ############
depthSensor = DepthSensor()
##########################

####### BATTERY ##########
batteryMonitor = BatteryMonitor()
batteryReadings = [-99,-99,-99,-99]
##########################

####### TEMPERATURE ######
temperatureMonitor = TemperatureMonitor()
temps = [-99,-99,-99,-99]
##########################

###### LIGHTS ##########

if config["lights"] == "GPIO":
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(19, GPIO.OUT)
    GPIO.setup(26, GPIO.OUT)
elif config["lights"] == "PWM":
    # set PWM channel
    print("Lights are in PWM mode")

########################

pwm = None;
app = Flask(__name__)



# Check internet access
def internet_on():
    i = False
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        i = True
    except urllib2.URLError as err:
        i = False
    return i


@app.route("/")
def hello():
    """Just saying hi"""
    return "Hello World!"


@app.route('/camera/start')
def camera_start():
    global handle, PHONE_IP, CAMERA_THREAD, PHONE_LAT, PHONE_LONG,PILOT_W,PILOT_H
    PHONE_IP = request.args.get("ip")
    PHONE_LAT = request.args.get("lat")
    PHONE_LONG = request.args.get("longitude")
    PILOT_H = request.args.get("h")
    PILOT_W = request.args.get("w")

    resp = "Starting camera"

    if PHONE_LAT == None or PHONE_LONG == None:
        PHONE_LAT = -1
        PHONE_LONG = -1

    #if CAMERA_THREAD.isAlive():
        # already streaming so doing nothing
        #print("Already streaming...")
        # resp = "Already streaming"
    #else:
        # handle = CAMERA_THREAD.start()
        #create_divelog_entry("1", PHONE_LAT, PHONE_LONG)

    return resp


@app.route('/camera/stop')
def camera_stop():
    global handle, PHONE_IP, CAMERA_THREAD, PHONE_LAT, PHONE_LONG
    ip = request.args.get("ip")
    create_divelog_entry("0", PHONE_LAT, PHONE_LONG)
    # CAMERA_THREAD.stopStreaming()
    return 'Stopping camera'


@app.route('/record/start')
def record_start():
    global factory,PHONE_LAT,PHONE_LONG
    factory.protocol.startRecording(PHONE_LAT,PHONE_LONG)
    #start_recording()
    return 'Recording'


@app.route('/record/stop')
def record_stop():
    stop_recording()
    return 'Stopped recording'


@app.route('/battery')
def get_battery_status():
    global batteryMonitor
    cutoff = request.args.get("cutoff")
    battery_level = batteryMonitor.read_raw()

    # shift all values back
    batteryReadings[3] = batteryReadings[2]
    batteryReadings[2] = batteryReadings[1]
    batteryReadings[1] = batteryReadings[0]

    # check if just booted up
    if [batteryReadings[0] == -99]:
        batteryReadings[3] = batteryMonitor.read_raw()
        batteryReadings[2] = batteryMonitor.read_raw()
        batteryReadings[1] = batteryMonitor.read_raw()
        batteryReadings[0] = batteryMonitor.read_raw()

    # calculate average battery reading
    avg_batteryReading = (batteryReadings[3] + batteryReadings[2] + batteryReadings[1]) / 3
    # check if bad val
    if (abs(battery_level - batteryReadings[0]) > 3000):
        # if bad val, replace temp[0] with avg battery reading
        batteryReadings[0] = avg_batteryReading
    else:
        # good val so make it current temp
        batteryReadings[0] = battery_level


    # default cutoff should be 21785
    if batteryReadings[0] < int(cutoff) :
        print("WARNING: battery is critically low. Shutting down")
        shutdown()


    return str(batteryReadings[0])

@app.route('/esc/calibrate')
def get_esc_calibrate():
    call("python /home/pi/SERVER/diag/calibrate_esc.py", shell=True)
    return "200"

@app.route('/depth')
def get_depth():
    global depthSensor
    return str(depthSensor.read_depth())


@app.route('/depth/pressure')
def get_depth_presure():
    global depthSensor
    return str(depthSensor.read_pressure())


@app.route('/depth/raw')
def get_depth_raw():
    global depthSensor

    return str(depthSensor.read_raw())


@app.route('/depth/offset')
def get_depth_raw_psi():
    global depthSensor
    return str(depthSensor.read_offset())


@app.route('/depth/calibrate')
def calibrate_depth():
    global depthSensor
    depthSensor.calibrate()
    return '200'


@app.route('/temperature')
def get_temperature():
    global temperatureMonitor,temps

    cutoff = request.args.get("cutoff")
    nw = subprocess.Popen(["vcgencmd measure_temp"], stdout=subprocess.PIPE,shell=True)
    output = nw.communicate()[0]
    output_parts = output.split("=")
    pi_temp = output_parts[1][:-3]

    thermistor_temp = temperatureMonitor.read_raw()
    # shift all values back
    temps[3] = temps[2]
    temps[2] = temps[1]
    temps[1] = temps[0]

    # check if just booted up
    if[temps[0] == -99]:
        temps[3] = temperatureMonitor.read_raw()
        temps[2] = temperatureMonitor.read_raw()
        temps[1] = temperatureMonitor.read_raw()
        temps[0] = temperatureMonitor.read_raw()

    # calculate average temp
    avg_temp = (temps[3]+temps[2]+temps[1]) / 3
    # check if bad val
    if(abs(thermistor_temp - temps[0]) > 4 ):
        # if bad val, replace temp[0] with avg temp
        temps[0] = avg_temp
    else:
        # good val so make it current temp
        temps[0] = thermistor_temp

    # check if at cutoff
    if temps[0] > int(cutoff) :
        print("WARNING: battery temperature is critically high. Shutting down")
        shutdown()

    return str(pi_temp+","+str(temps[0]))


@app.route('/heading')
def get_heading():
    # h = random.randint(135, 142)
    global magnetometer
    h = magnetometer.get_heading()
    return str(h)


@app.route('/pitch')
def get_pitch():
    global accelerometer
    return str(accelerometer.get_pitch())

@app.route('/roll')
def get_roll():
    global accelerometer
    return str(accelerometer.get_roll())

@app.route('/lights/on')
def lights_on():
    global GPIO,pwm

    if config["lights"] == "GPIO":
        GPIO.output(19, True)
        GPIO.output(26, True)
    elif config["lights"] == "PWM":
        pwm.set_pwm(3, 0, int(600))
    return "200"


@app.route('/lights/off')
def lights_off():
    global GPIO,pwm
    if config["lights"] == "GPIO":
        GPIO.output(19, False)
        GPIO.output(26, False)
    elif config["lights"] == "PWM":
        pwm.set_pwm(3, 0, int(0))

    return "200"


@app.route('/calibrate')
def start_calibrate():
    global calibrator
    direction = request.args.get("direction")
    if direction == "xmin":
        calibrator.calibrate_accelerometer_x_min()
    elif direction == "xmax":
        calibrator.calibrate_accelerometer_x_max()
    elif direction == "ymin":
        calibrator.calibrate_accelerometer_y_min()
    elif direction == "ymax":
        calibrator.calibrate_accelerometer_y_max()
    elif direction == "zmin":
        calibrator.calibrate_accelerometer_z_min()
    elif direction == "zmax":
        calibrator.calibrate_accelerometer_z_max()
    elif direction == "calc":
        calibrator.xandycal()
        calibrator.write_calibration()
    elif direction == "mag":
        calibrator.calibrate_magnetometer(duration=20,interval=.1)
    elif direction == "save":
        calibrator.write_calibration()

    # calibrator.calibrate()
    return "200"


@app.route('/observer/start')
def get_observer_start():
    global OBSERVER_IP, CAMERA_THREAD,OBSERVER_H,OBSERVER_W
    OBSERVER_H = request.args.get("h")
    OBSERVER_W = request.args.get("w")
    OBSERVER_IP = request.args.get("ip")
    CAMERA_THREAD.startObserver()
    return "200"


@app.route('/observer/stop')
def get_observer_stop():
    stop_observer()
    return "200"


@app.route('/flights')
def get_flights():
    global DIVE_LOG
    flights = []
    with open(DIVE_LOG, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\n', quotechar='|')
        # for row in reader:
        #    print ', '.join(row)
        flights = list(reader)
    return jsonify(flights)


@app.route('/flights/recordings')
def get_flight_recordings():
    f = find_recordings()
    return jsonify(f)

@app.route('/flights/recordings/delete')
def get_delete_recording():
    recording = request.args.get("rec")
    recording_path = "server/static/recordings/"+recording
    os.remove(recording_path)
    return "200"

@app.route('/disk/utilization')
def get_disk_utilization():
    df = subprocess.Popen(["df", "."], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    device, size, used, available, percent, mountpoint = output.split("\n")[1].split()
    formatted_percent = percent.rstrip('%')
    return formatted_percent

@app.route('/disk/usage_available')
def get_disk_usage_available():
    df = subprocess.Popen(["df", "."], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    device, size, used, available, percent, mountpoint = output.split("\n")[1].split()
    return available

@app.route("/manager")
def get_manager():
    flight_records = find_recordings()

    return render_template("manager.html", title="Manager", flight_records=flight_records)

@app.route('/reboot')
def get_reboot():
    command = "/sbin/reboot"
    call(command, shell=True)
    return "200"


@app.route('/shutdown')
def get_shutdown():
    print("/shutdown called. Shutting down")
    shutdown()
    return "200"

@app.route('/upload')
def upload():
    VIDEO_FILE = "/home/pi/launch_log.txt"

    S3_ACCESS_KEY = ""
    S3_SECRET_KEY = ""
    USER_ID = ""
    TIMESTAMP = ""
    video_number = 0

    # check for internet
    if (internet_on() == False):
        # no internet, return an error
        return "400"

    # upload endpoint
    #conn = tinys3.Connection(S3_ACCESS_KEY, S3_SECRET_KEY, tls=True)

    # try to upload
    #f = open(VIDEO_FILE, 'rb')
    #conn.upload(USER_ID + "_" + TIMESTAMP + "_" + video_number, f, 'videos')

    ### after upload tell Fathom Community Portal API ###
    # create payload object for database record
    payload = {}
    payload['max_depth'] = 99
    payload['capture_time'] = "TODO"
    payload['latitude'] = "TODO"
    payload['longitude'] = "TODO"
    # payload['tags'] = "TODO"

    # make request
    url = 'http://localhost:3000/upload'
    r = requests.post(url, data=json.dumps(payload))



    # report status

    return "200"


@app.route('/update')
def update():
    res = ""
    print("Before tryUpdate()")
    call("sudo python server/update_server.py", shell=True)
    res = "200"

    print("After tryUpdate()...")
    return res

@app.route('/system/status')
def system_status():
    return_status = "200"
    # check if updating
    UPDATING_INDICATOR="/home/pi/SERVER/UPDATING.LOCK"
    isUpdating = os.path.isfile(UPDATING_INDICATOR)
    if isUpdating:
        return_status = "UPDATING"

    return return_status

@app.route('/system/wifi')
def system_wifi():
    turnOn = request.args.get("on")
    upOrDown = "down"
    if(turnOn == True or turnOn == "true"):
        upOrDown = "up"
    call("sudo ifconfig wlan0 "+upOrDown, shell=True)
    return "200"



@app.route('/system/ethernet')
def system_ethernet():
    turnOn = request.args.get("on")
    upOrDown = "up"
    if (turnOn == False or turnOn == "false"):
        upOrDown = "down"
    call("sudo ifconfig eth0 " + upOrDown, shell=True)
    return "200"

def start_recording():
    print("START_RECORDING")
    global camera_lock
    global start_saving, saving, stop_saving, CAMERA_THREAD
    with camera_lock:
        start_saving = True
        saving = False
        stop_saving = False
    CAMERA_THREAD.startRecording()

@app.route('/convert/all')
def convert_videos():
    call("bash /home/pi/SERVER/server/convert_videos.sh",shell=True)
    return "200"

@app.route('/network/available')
def network_available():
    call("sudo ifconfig wlan0 up ", shell=True)
    time.sleep(4)
    nw = subprocess.Popen(["sudo iwlist wlan0 scan | grep ESSID"], stdout=subprocess.PIPE,shell=True)
    output = nw.communicate()[0]
    networks =  output.split("ESSID:")
    return jsonify(networks)

@app.route('/network/add')
def network_add():
    network = request.args.get("network")
    password = request.args.get("password")
    call("bash network_add.sh "+str(network)+" "+str(password),shell=True)
    return "200"

@app.route('/network/isConnected')
def get_network_isConnected():
    return str(internet_on())

@app.route('/logs/upload')
def get_logs_upload():

    # get the ticket id
    TICKET_ID = request.args.get("ticket")
    LOG_FILE = "/home/pi/launch_log.txt"

    S3_ACCESS_KEY=""
    S3_SECRET_KEY=""

    # check for internet
    if (internet_on() == False):
        # no internet, return an error
        return "400"

    # upload endpoint
    #conn = tinys3.Connection(S3_ACCESS_KEY, S3_SECRET_KEY, tls=True)

    # try to upload
    #f = open(LOG_FILE, 'rb')
    #conn.upload(TICKET_ID+"_"+LOG_FILE, f, 'tickets')


    # report status

    return "200"

@app.route('/drone/uptime')
def get_uptime():
    return str(calculateUptime())

@app.route('/drone/flightcount')
def get_flightcount():
    return str(calculateFlights())

@app.route('/drone/flighttime')
def get_flighttime():
    return str(calculateFlighttime())

@app.route('/drone/info')
def get_droneInfo():
    droneInfo = {}

    uptime = calculateUptime()
    flightcount = calculateFlights()
    flighttime=calculateFlighttime()

    droneInfo['uptime'] = uptime
    droneInfo['flightcount'] = flightcount
    droneInfo['flighttime'] = flighttime
    return jsonify(droneInfo)


@app.route('/version')
def get_version():
    version = "0.1"
    return version

def stop_recording():
    global start_saving, saving, stop_saving, CAMERA_THREAD
    with camera_lock:
        stop_saving = True
        start_saving = False
        saving = False
    CAMERA_THREAD.stopRecording()

def stop_observer():
    global stop_observer_connection, CAMERA_THREAD
    stop_observer_connection = True
    CAMERA_THREAD.stopObserver()


def start_rest_api():
    app.run(host='0.0.0.0', port=80, debug=True)



def create_divelog_entry(entry_type, lat, longitude):
    global DIVE_LOG
    line1 = entry_type + "," + time.strftime("%m_%d_%H_%M_%S") + "," + str(lat) + "," + str(longitude)
    target = open(DIVE_LOG, 'a')
    target.write(line1)
    target.write("\n")
    target.close()



def find_recordings():
    f = []
    mypath = "server/static/recordings"
    for (dirpath, dirnames, filenames) in walk(mypath):
        # f.extend(filenames)
        for (file) in sorted(filenames):
            if file.endswith(".mp4") or file.endswith(".h264"):
                flight = Flight(file)
                f.append(flight.serialize())
        break
    return f


def characterCount(filename):
    count=0;
    in_file = open(filename, 'r')
    data = in_file.read()
    count = len(data)
    return count

def calculateUptime():
    return characterCount("/home/pi/SERVER/server/uptime.txt")

def calculateFlights():
    #return characterCount("home/pi/SERVER/server/flights.txt")
    return "10"

def calculateFlighttime():
    return characterCount("/home/pi/SERVER/server/flighttime.txt")

def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.

def sorted_ls(path):
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))

def shutdown():
    global pwm, allow_shutdown
    if allow_shutdown:

        pwm.set_all_pwm(0,0)
        # shutdown
        command = "/sbin/shutdown"
        call(command, shell=True)


if __name__ == "__main__":

    #### STREAMING CONSTANTS ####
    PHONE_IP = None
    PHONE_PORT = 8000
    PILOT_W = 640
    PILOT_H = 360
    MCAST_GRP = "192.168.1.71"
    MCAST_PORT = 8010

    OBSERVER_W = 640
    OBSERVER_H = 360
    OBSERVER_IP = None
    OBSERVER_PORT = 8010

    DIVE_LOG = "divelog.csv"
    PHONE_LAT = -1
    PHONE_LONG = -1


    setupPWM()
    start_saving = False
    stop_saving = False
    saving = False
    start_streaming = True
    stop_streaming = False
    start_observer_connection = False
    stop_observer_connection = False

    if len(sys.argv) > 1:
        if sys.argv[1] == "debug":
            allow_shutdown = False
    else :
        allow_shutdown = True


    handle = None
    REST_API_THREAD = threading.Thread(target=start_rest_api())
    REST_API_THREAD.start()
