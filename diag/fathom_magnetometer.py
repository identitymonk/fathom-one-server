import time
import sys
from LSM9DS1 import LSM9DS1


##### Magnetometer OBJECT CLASS ####
class Magnetometer(object):
    calibration_file = 'calibration'


    def __init__(self, calibration_file,imu):
        self.calibration_file = calibration_file
        self.imu = imu
    def get_heading(self):
        return self.imu.heading()
