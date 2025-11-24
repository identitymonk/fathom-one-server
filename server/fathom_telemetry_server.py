from LSM9DS1 import LSM9DS1, Axis
from fathom_accelerometer import Accelerometer
from fathom_calibrator import Calibrator
from fathom_depth_sensor import DepthSensor
from fathom_magnetometer import Magnetometer
from subprocess import call
import socket
from time import sleep

CALIBRATION_FILE = 'calibration'
calibrator = Calibrator(CALIBRATION_FILE)
ac = Accelerometer(CALIBRATION_FILE,calibrator.getIMU())
magnetometer = Magnetometer(CALIBRATION_FILE, calibrator.getIMU())
depthSensor = DepthSensor()




call(["fuser", "9876/tcp", "-k"])
observer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
observer_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

while True:

    pitch = ac.get_pitch()
    roll = ac.get_roll()
    depth = depthSensor.read_depth()
    heading = magnetometer.get_heading()
    message = str(pitch) + "," + str(roll) + "," + str(depth) + "," + str(heading)
    observer_socket.sendto(str(message),('224.1.1.1', 9876))

    #print("sent "+str(message))
    sleep(.25)









