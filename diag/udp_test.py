from subprocess import call
import socket
from time import sleep

call(["fuser", "8005/tcp", "-k"])
#observer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#observer_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8000))
count = 0
while True:
    server_socket.sendto(str(count),('192.168.1.71', 16001))
    count=count+1
    print("sent "+str(count))
    sleep(1)
