from LSM9DS1 import LSM9DS1, Axis


##### Accelerometer OBJECT CLASS ####
class Accelerometer(object):
    calibration_file = 'calibration'


    def __init__(self, calibration_file,imu):
        self.calibration_file = calibration_file
        self.imu = imu
        #self.imu = LSM9DS1(axis_order=(Axis.Y, Axis.X, Axis.Z), reverse_axis=(False, False, False))
    def get_pitch(self):
        return self.imu.pitch()
    def get_roll(self):
        return self.imu.roll();

    def load_calibration(self):
        with open('calibration') as f:
            lines = f.read().splitlines()

        floats = lambda l: [float(i) for i in l]
        accel_cal = floats(lines[0].split(' '))
        gyro_cal = floats(lines[1].split(' '))
        mag_cal = floats(lines[2].split(' '))
        print(accel_cal, gyro_cal, mag_cal)
        self.imu.xg.offset_accel = accel_cal
        self.imu.xg.offset_gyro = gyro_cal
        self.imu.mag.offset = mag_cal