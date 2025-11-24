from subprocess import call
import socket
from time import sleep



call(["fuser", "9876/tcp", "-k"])
observer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
observer_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)


def generate_pitch():
    return 5.0

def generate_depth():
    return 0.0

def generate_roll():
    return 10.0

def generate_heading():
    return 180.0


while True:

    pitch = generate_pitch()
    roll = generate_roll()
    depth = generate_depth()
    heading = generate_heading()
    message = str(pitch) + "," + str(roll) + "," + str(depth) + "," + str(heading)
    observer_socket.sendto(str(message),('224.1.1.1', 9876))

    sleep(1)









