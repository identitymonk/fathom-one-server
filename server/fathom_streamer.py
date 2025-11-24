##### STEAMING OBJECT CLASS ####
class PilotStreamer(object):
    def __init__(self, socket,PHONE_IP,PHONE_PORT):
        self.socket = socket
        self.PHONE_IP = PHONE_IP
        self.PHONE_PORT = PHONE_PORT

    def write(self, buf):
        # Need to define MCAST_GRP and MCAST_PORT somewhere
        self.socket.sendto(buf, (self.PHONE_IP, self.PHONE_PORT))

    def flush(self):
        print "Flushing pilot stream"

##################################

##### OBSERVER STREAMING OBJECT CLASS ####
class ObserverOutput(object):

    def __init__(self, socket, MCAST_GRP, MCAST_PORT):
        self.socket = socket
        self.MCAST_GRP = MCAST_GRP
        self.MCAST_PORT = MCAST_PORT

    def write(self, buf):
        self.socket.sendto(buf, (self.MCAST_GRP, self.MCAST_PORT))


##################################