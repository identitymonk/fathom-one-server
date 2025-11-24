import base64
import datetime
import json
import os
import socket
import threading
import time
from subprocess import call

import picamera
import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, \
    listenWS

from fathom_streamer import PilotStreamer,ObserverOutput

##### SETUP UDP STREAMING ########
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8000))
# server_socket.listen(8000)

####################################

######## SETUP OBSERVING #######
call(["fuser", "8005/tcp", "-k"])
observer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
observer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
observer_socket.bind(('0.0.0.0', 8005))

####################################

camwrite = None
cam = None
clients = []
DEFAULT_CAMERA_RESOLUTION = (400,400)
DEFAULT_RECORDING_RESOLUTION = (1920, 1080)
########### SETUP CAMERA THREAD ###
class CameraThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def startObserver(self):
        global cam, MCAST_GRP, MCAST_PORT, OBSERVER_IP, OBSERVER_PORT,OBSERVER_H,OBSERVER_W
        cam.start_recording(ObserverOutput(observer_socket, OBSERVER_IP, OBSERVER_PORT), 'h264', splitter_port=1,
                            resize=(int(OBSERVER_W), int(OBSERVER_H)), quality=20)

    def stopObserver(self):
        global cam
        cam.stop_recording(splitter_port=1)

    def startRecording(self):
        global cam, PHONE_LAT, PHONE_LONG
        recording_filename = build_recording_filename(PHONE_LAT, PHONE_LONG)
        cam.start_recording(recording_filename, splitter_port=2, resize=(720, 360), bitrate=4000000)

    def stopRecording(self):
        global cam
        cam.stop_recording(splitter_port=2)

    def stopStreaming(self):
        global cam
        cam.stop_recording(splitter_port=0)
        self._stop.set()

    def run(self):
        global cam
        global camera_lock
        global start_streaming, stop_streaming, start_saving, stop_saving, saving
        global observer_socket
        global start_observer_connection, stop_observer_connection
        global PHONE_IP, PHONE_PORT, PILOT_H, PILOT_W
        with picamera.PiCamera() as camera:
            cam = camera
            cam.resolution = (1920, 1080)
            cam.vflip = True
            cam.hflip = True
            # camera.framerate = 30
            print(PILOT_H)
            print(PILOT_W)
            cam.start_recording(PilotStreamer(server_socket, PHONE_IP, PHONE_PORT), 'h264', resize=(int(PILOT_W), int(PILOT_H)), splitter_port=0, bitrate=22000000)
            cam.wait_recording(12000,splitter_port=0)
        return True



##################################


########## RTC OUTPUT ############
class MyOutput(object):
    def __init__(self):
        self.size = 0

    def write(self, s):
        self.size += len(s)
        camwrite(s)

    def flush(self):
        print('%d bytes would have been written' % self.size)
##################################


##### BROADCAST SERVER PROTOCOL ##
class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        global cam
        if not isBinary:
            msg = "{} from {}".format(payload.decode('utf8'), self.peer)
            # self.factory.broadcast(msg)
            cmd = json.loads(payload)
            if (cmd.has_key("recording")):
                print("Recording command recieved")
                print("should record: "+str(cmd["recording"]))
                if (cmd["recording"] == "start"):
                    print("START RECORDING")
                    self.startRecording(cmd["latitude"],cmd["longitude"],cmd["when"])
                else:
                    print("STOP RECORDING")
                    self.stopRecording()

            if (cmd.has_key("cmd")):
                if (cmd["cmd"] == "showpreview"):
                    cam.start_preview()
                if (cmd["cmd"] == "hidepreview"):
                    cam.stop_preview()
            if (cmd.has_key("framerate")):
                cam.stop_recording()
                cam.framerate = int(cmd["framerate"])
                cam.start_recording(MyOutput(), format='mjpeg', bitrate=10000000, quality=10)

    def startRecording(self,phone_lat, phone_long,when):
        global cam
        recording_filename = build_recording_filename(phone_lat, phone_long,when)
        cam.start_recording(recording_filename, splitter_port=2, resize=DEFAULT_RECORDING_RESOLUTION, bitrate=4000000)

    def stopRecording(self):
        global cam
        cam.stop_recording(splitter_port=2)

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        print(reason)
        print("Connection lost")
        self.factory.unregister(self)
##################################

############### WEBSERVER ########
class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url, debug=True, debugCodePaths=True):
        WebSocketServerFactory.__init__(self, url)
        global clients, cam, camwrite
        self.clients = clients
        self.tickcount = 0

        camwrite = self.broadcast
        cam = picamera.PiCamera()
        cam.framerate = 26
        cam.vflip = True
        cam.hflip = True
        cam.resolution =  DEFAULT_CAMERA_RESOLUTION
        cam.brightness = 55
        cam.saturation = 10
        #cam.exposure_mode = 'night'

    def register(self, client):
        if (len(self.clients) == 0):
            cam.start_recording(MyOutput(), format='mjpeg', bitrate=1500000)
        if not client in self.clients:
            print("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)
        if (len(self.clients) <= 0):
            cam.stop_recording()

    def broadcast(self, msg):
        # print("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            #c.sendMessage(msg.encode('base64'))
            c.sendMessage(base64.b64encode(msg))

            #print(msg.encode('base64'));
            #print("##################################NEXT###########");

            #print("message sent to {}".format(c.peer))




#################################

def setupWebServer():
    ServerFactory = BroadcastServerFactory
    debug=True
    factory = ServerFactory("ws://0.0.0.0:9000",
                            debug=debug,
                            debugCodePaths=debug)

    factory.protocol = BroadcastServerProtocol
    listenWS(factory)



def build_recording_filename(lat, longitude,when):
    converted_time = int(when)/1000
    formatted_time = time.strftime("%m_%d_%H_%M_%S", time.gmtime(converted_time))

    filename = "server/static/recordings/" + formatted_time + "_" + str(lat) + "_" + str(longitude) + ".h264"

    return filename

if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        log.startLogging(sys.stdout)
        debug = True
    else:
        debug = False
    global cam
    ServerFactory = BroadcastServerFactory
    # ServerFactory = BroadcastPreparedServerFactory

    factory = ServerFactory("ws://0.0.0.0:9000",
                            debug=debug,
                            debugCodePaths=debug)

    factory.protocol = BroadcastServerProtocol
    #factory.setProtocolOptions()
    listenWS(factory)

    #print(os.path.dirname(os.path.abspath(__file__)))

    webdir = File(str(os.path.dirname(os.path.abspath(__file__))) + "/www")
    web = Site(webdir)
    reactor.listenTCP(8080, web)

    reactor.run()
    cam.stop_recording()
    cam.close()