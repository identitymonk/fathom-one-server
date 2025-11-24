import socket
import Adafruit_PCA9685
import threading


pwm = None
############### PWM CONSTANTS #####################
# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096
servo_neutral = 375
thrust = 375
thruster_scale = 1
scale_lock = None
###################################################

#### STREAMING CONSTANTS ####
MCAST_GRP="192.168.0.101"
MCAST_PORT = 8000



server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8001))
#server_socket.listen(5)


def setupPWM():
    global pwm
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)

def setupLock():
    global scale_lock
    scale_lock = threading.Lock()


def send_thrust_to_esc(val):
    global scale_lock,thruster_scale,thrust
    global servo_min,servo_max,servo_neutral

    pwm.set_pwm(3,0,int(val))
    #pwm.set_all_pwm(0,val)
    print("SENDING PITCH: ")
    print(val)


setupPWM()
setupLock()


while True:
    while True:
       data, addr = server_socket.recvfrom(1024) # buffer size is 1024 bytes
       send_thrust_to_esc(int(float(data)))
       print "received message:", data 
server_socket.close() 
