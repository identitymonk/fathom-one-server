import time
import sys
from LSM9DS1 import LSM9DS1, Axis


##### CALIBRATION OBJECT CLASS ####
class Calibrator(object):
    calibration_file = 'calibration'


    def __init__(self, calibration_file):
        self.calibration_file = calibration_file
        self.xmin = 0
        self.ymin = 0
        self.xmax = 0
        self.ymax = 0
        self.zmin = 0
        self.zmax = 0
        self.xcal = 0
        self.ycal = 0
        self.zycal = 0
        self.imu = LSM9DS1(axis_order=(Axis.X, Axis.Y, Axis.Z), reverse_axis=(False, False, True))

        try:
            self.load_calibration()
        except Exception as e:
            print("No calibration exists")

    def calibrate_accelerometer_x_min(self):
        #print('X-min. Press enter')
        #sys.stdin.readline()
        (self.xmin, _, _) = self.imu.xg.read_accel_raw()

    def calibrate_accelerometer_y_min(self):
        #print('Y-min. Press enter')
        #sys.stdin.readline()
        (_, self.ymin, _) = self.imu.xg.read_accel_raw()

    def calibrate_accelerometer_x_max(self):
        #print('X-max. Press enter')
        #sys.stdin.readline()
        (self.xmax, _, _) = self.imu.xg.read_accel_raw()

    def calibrate_accelerometer_y_max(self):
        #print('Y-max. Press enter')
        #sys.stdin.readline()
        (_, self.ymax, _) = self.imu.xg.read_accel_raw()

    def calibrate_accelerometer_z_min(self):
        #print('Z-min. Press enter')
        #sys.stdin.readline()
        (_, _, self.zmin) = self.imu.xg.read_accel_raw()

    def calibrate_accelerometer_z_max(self):
        #print('Z-max. Press enter')
        #sys.stdin.readline()
        (_, _, self.zmax) = self.imu.xg.read_accel_raw()

    def xandycal(self):
        self.xcal = -((self.xmax + self.xmin) / 2)
        self.ycal = -((self.ymax + self.ymin) / 2)
        self.zcal = -((self.zmax + self.zmin) / 2)
        self.imu.xg.offset_accel = [self.xcal, self.ycal, self.zcal]
        print('Done.')
        print('accel offset', self.imu.xg.offset_accel)


    def calibrate_accelerometer(self,imu):
        print('Calibrating accelerometer')
        self.calibrate_accelerometer_x_min(imu)
        self.calibrate_accelerometer_x_max(imu)
        self.calibrate_accelerometer_y_min(imu)
        self.calibrate_accelerometer_y_max(imu)
        self.calibrate_accelerometer_z_min(imu)
        self.calibrate_accelerometer_z_max(imu)
        self.xandycal(imu)

    #### MAGNETOMETER ####################
    def calibrate_magnetometer(self, duration=20, interval=0.1):
        xvals = []
        yvals = []
        zvals = []

        print('Calibrating magnetometer')
        print("Collecting data", )
        sys.stdout.flush()
        for i in range(0, int(duration / interval)):
            r = self.imu.mag.read_raw()
            xvals.append(r[0])
            yvals.append(r[1])
            zvals.append(r[2])
            print(".", )
            sys.stdout.flush()
            time.sleep(interval)
        print()
        self.imu.mag.offset[0] = -((max(xvals) + min(xvals)) / 2)
        self.imu.mag.offset[1] = -((max(yvals) + min(yvals)) / 2)
        self.imu.mag.offset[2] = -((max(zvals) + min(zvals)) / 2)
        print("Done")

    def write_calibration(self):
        with open('calibration', 'w') as f:
            f.write(' '.join([str(i) for i in self.imu.xg.offset_accel]))
            f.write('\n')
            f.write('0 0 0')
            f.write('\n')
            f.write(' '.join([str(i) for i in self.imu.mag.offset]))

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

    def calibrate(self):
        self.calibrate_accelerometer(self.imu)
        self.calibrate_magnetometer(self.imu)

        with open('calibration', 'w') as f:
            f.write(' '.join([str(i) for i in imu.xg.offset_accel]))
            f.write('\n')
            f.write('0 0 0')
            f.write('\n')
            f.write(' '.join([str(i) for i in imu.mag.offset]))
        print()

    def getIMU(self):
        return self.imu