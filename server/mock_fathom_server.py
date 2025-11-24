import threading

from twisted.python import log
import sys
from flask import Flask, render_template
from flask import jsonify,request
import time
from os import walk
import random
from fathom_flight import Flight
import csv
import urllib2
import requests
import boto3

import subprocess
import update_server


factory = None
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/manager")
def get_manager():
    videos = \
        [{"start": "18:25",
          "end": "18:35",
          "date": "January 11",
          "location":{
              "lat": "43.55",
              "longitude": "-85.110"
            },
          "filename":"12_09_14_30_recording.h264"
          }
        ,{"start": "16:15",
          "end": "16:35",
          "date": "January 10",
          "location":{
              "lat": "43.55",
              "longitude": "-85.110"
            },
          "filename": "12_09_14_30_recording.h264"
          }
        ]
    return render_template("manager.html",title="Manager",videos=videos)

@app.route('/stream/start')
def stream_start():
    ip = request.args.get("ip")
    if ip == None:
        ip = "BLAH"
    start_streaming(ip)
    return ip

@app.route('/record/start')
def record_start():
    global factory
    PHONE_LAT = "-2"
    PHONE_LONG = "-3"
    factory.protocol.startRecording(PHONE_LAT, PHONE_LONG)

    #start_time = request.args.get("when")
    #latitude = request.args.get("lat")
    #longitude = request.args.get("long")
    #start_recording(start_time,latitude,longitude)
    return 'Recording'

@app.route('/battery')
def get_battery_status():
    return '100'

@app.route('/depth')
def get_depth():
    d = random.randint(0,9)
    return str(d)

@app.route('/temperature')
def get_temperature():
    t = random.randint(29,32)
    return str(t)

@app.route('/heading')
def get_heading():
    h = random.randint(135,142)
    return str(h)

@app.route('/lights/on')
def lights_on():
    # todo: turn on lights
    return "200"

@app.route('/lights/off')
def lights_off():
    # todo: turn off lights
    return "200"


@app.route('/disk/utilization')
def get_disk_utilization():

    return str(20)

@app.route('/disk/usage_available')
def get_disk_usage_available():

    return "TODO"

@app.route('/flights')
def get_flights():
    flights = []
    with open('flights.csv', 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\n', quotechar='|')
        #for row in reader:
        #    print ', '.join(row)
        flights = list(reader)
    return jsonify(flights)


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

@app.route('/flights/recordings')
def get_flight_recordings():
    f = find_recordings()
    return jsonify(f)

def start_recording(start_time,latitude,longitude):
    print("START_RECORDING")
    print("Recording at "+start_time+"...lat: "+latitude+" ...long:"+longitude)
    # print (time.strftime("%H_%M_%S"))

def start_camera():
    print("START_CAMERA")
    return True

def start_streaming(ip):
    print("Starting stream")
    filename = "flights.csv"
    line1 = "1,"+time.strftime("%m_%d_%H_%M_%S")
    print "Opening the file..."
    target = open(filename, 'a')
    target.write(line1)
    target.write("\n")
    target.close()

@app.route('/update')
def update():
    update_server.tryUpdate()
    return "200"


# Check internet access
def internet_on():
    i = False
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        i = True
    except urllib2.URLError as err:
        i = False
    return i


@app.route('/upload')
def upload():
    s3 = boto3.resource('s3')
    #VIDEO_FILE = "/Users/bkaiser/github/Fathom Tools/flights.csv"
    #VIDEO_FILE ="/Users/bkaiser/Downloads/upload_test.png"
    RECORDING_DIR = "/Users/bkaiser/Downloads/"
    FILE_NAME = request.args.get("file")
    if FILE_NAME == None:
        return "404"
    else:
        VIDEO_FILE = RECORDING_DIR + FILE_NAME

    S3_ACCESS_KEY = ""
    S3_SECRET_KEY = ""
    USER_ID = "5993664863347a8a1f180875"
    TIMESTAMP = time.strftime("%d_%m_%Y_%H_%M_%S",time.localtime())
    CAPTURE_TIME = time.strftime("%d_%m_%Y_%H_%M_%S",time.localtime())
    latitude = "43.9510"
    longitude = "-85.6011"
    uploaded_filename = "videos/"+USER_ID + "_" + str(TIMESTAMP) + "_" + str(FILE_NAME)
    S3_BASE = "https://s3.us-east-2.amazonaws.com/fathomdronepublic/"
    print(TIMESTAMP)
    print(VIDEO_FILE)
    video_number = 0

    # check for internet
    if (internet_on() == False):
        # no internet, return an error
        return "400"

    # upload endpoint
    #conn = tinys3.Connection(S3_ACCESS_KEY, S3_SECRET_KEY, default_bucket='fathomdronepublic')
    #s3.meta.client.upload_file(VIDEO_FILE, 'fathomdronepublic', 'hello.txt')
    s3.Object('fathomdronepublic',uploaded_filename ).put(Body=open(VIDEO_FILE, 'rb'))
    # try to upload
    #f = open(VIDEO_FILE, 'rb')
    #conn.upload(USER_ID + "_" + str(TIMESTAMP) + "_" + str(FILE_NAME), f, 'fathomdronepublic')
    #conn.upload("BLAH",f)
    ### after upload tell Fathom Community Portal API ###
    # create payload object for database record
    payload = [('owner', USER_ID),
               ('max_depth', 99),
               ('capture_time', CAPTURE_TIME),
               ('latitude', latitude),
               ('longitude', longitude),
               ('link', S3_BASE + uploaded_filename)
               ]
    # payload['tags'] = "TODO"

    # make request
    url = 'http://localhost:3000/api/videos/upload'
    r = requests.post(url, data=payload)



    # report status

    return "200"

@app.route('/network/available')
def network_available():
    networks = []
    nw = subprocess.Popen(["iwlist", "wlan0", "scan"], stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', 'ESSID'), stdin=nw.stdout)
    networks_raw = output.replace("ESSID:","").split("\n")
    for index in range(len(networks_raw)):
        networks.append(networks_raw[index].strip())
        print("network")

    return jsonify(networks)

@app.route('/network/isConnected')
def get_network_isConnected():
    isConnected = False
    isConnected = internet_on()
    return isConnected


def start_rest_api():
    app.run(host='0.0.0.0',port=9001,debug=True)
    print("AFTER")



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


def calculateUptime():
    return "500"

def calculateFlights():
    return "10"

def calculateFlighttime():
    return "125"

if __name__ == "__main__":
    log.startLogging(sys.stdout)
    print("Starting api...")
    REST_API_THREAD = threading.Thread(target=start_rest_api())
    REST_API_THREAD.start()


