import sys, json
from time import sleep
import base64
import picamera, threading
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, \
    listenWS

camwrite = None
cam = None
clients = []


class MyOutput(object):
    def __init__(self):
        self.size = 0

    def write(self, s):
        self.size += len(s)
        camwrite(s)

    def flush(self):
        print('%d bytes would have been written' % self.size)


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
            if (cmd.has_key("cmd")):
                if (cmd["cmd"] == "showpreview"):
                    cam.start_preview()
                if (cmd["cmd"] == "hidepreview"):
                    cam.stop_preview()
            if (cmd.has_key("framerate")):
                cam.stop_recording()
                cam.framerate = int(cmd["framerate"])
                cam.start_recording(MyOutput(), format='mjpeg', bitrate=10000000, quality=10)

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        print(reason)
        print("LOST")
        self.factory.unregister(self)


class RTCBroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url, debug=True, debugCodePaths=True):
        WebSocketServerFactory.__init__(self, url)
        global clients
        self.clients = clients
        self.tickcount = 0
        global cam, camwrite
        camwrite = self.broadcast
        cam = picamera.PiCamera()
        cam.framerate = 26
        cam.vflip = True
        cam.hflip = True
        cam.resolution = (400,400)
        #cam.exposure_mode = 'night'

    def register(self, client):
        if (len(self.clients) == 0):
            cam.start_recording(MyOutput(), format='mjpeg', bitrate=4000000)
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


if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        log.startLogging(sys.stdout)
        debug = True
    else:
        debug = False
    global cam
    ServerFactory = RTCBroadcastServerFactory
    # ServerFactory = BroadcastPreparedServerFactory

    factory = ServerFactory("ws://0.0.0.0:9000",
                            debug=debug,
                            debugCodePaths=debug)

    factory.protocol = BroadcastServerProtocol
    #factory.setProtocolOptions()
    listenWS(factory)

    webdir = File("./www")
    web = Site(webdir)
    reactor.listenTCP(80, web)

    reactor.run()
    cam.stop_recording()
    cam.close()