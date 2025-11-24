#!/usr/bin/env python3
from math import atan, atan2, pi, sqrt
import struct
from Adafruit_GPIO import I2C
import threading

# See:

####################################################################
# constants

class GyroRegisters():
    """
    Registers for the LSM9DS1 magnetometer I2c interface.

    These use the same names as found in the datasheet.
    """
    ACT_THS = 0x04
    ACT_DUR = 0x05
    INT_GEN_CFG_XL = 0x06
    INT_GEN_THS_X_XL = 0x07
    INT_GEN_THS_Y_XL = 0x08
    INT_GEN_THS_Z_XL = 0x09
    INT_GEN_DUR_XL = 0x0A
    REFERENCE_G = 0x0b
    INT1_CTRL = 0x0C
    INT2_CTRL = 0x0D
    WHO_AM_I = 0x0F
    CTRL_REG1_G = 0x10
    CTRL_REG2_G = 0x11
    CTRL_REG3_G = 0x12
    ORIENT_CFG_G = 0x13
    INT_GEN_SRC_G = 0x14
    OUT_TEMP_L = 0x15
    OUT_TEMP_H = 0x16
    STATUS_REG1 = 0x17
    OUT_X_L_G = 0x18
    OUT_X_H_G = 0x19
    OUT_Y_L_G = 0x1A
    OUT_Y_H_G = 0x1B
    OUT_Z_L_G = 0x1C
    OUT_Z_H_G = 0x1D
    CTRL_REG4 = 0x1E
    CTRL_REG5_XL = 0x1F
    CTRL_REG6_XL = 0x20
    CTRL_REG7_XL = 0x21
    CTRL_REG8 = 0x22
    CTRL_REG9 = 0x32
    CTRL_REG10 = 0x24
    INT_GEN_SRC_XL = 0x26
    STATUS_REG2 = 0x27
    OUT_X_L_XL = 0x28
    OUT_X_H_XL = 0x29
    OUT_Y_L_XL = 0x2A
    OUT_Y_H_XL = 0x2B
    OUT_Z_L_XL = 0x2C
    OUT_Z_H_XL = 0x2D
    FIFO_CTRL = 0x2E
    FIFO_SRC = 0x2F
    INT_GEN_CFG_G = 0x30
    INT_GEN_THS_XH_G = 0x31
    INT_GEN_THS_XL_G = 0x32
    INT_GEN_THS_YH_G = 0x33
    INT_GEN_THS_YL_G = 0x34
    INT_GEN_THS_ZH_G = 0x35
    INT_GEN_THS_ZL_G = 0x36
    INT_GEN_DUR_G = 0x37

class MagRegisters():
    OFFSET_X_REG_L_M = 0X05
    OFFSET_X_REG_H_M = 0x06
    OFFSET_Y_REG_L_M = 0x07
    OFFSET_Y_REG_H_M = 0x08
    OFFSET_Z_REG_L_M = 0x09
    OFFSET_Z_REG_H_M = 0x0A
    WHO_AM_I_M = 0x0F
    CTRL_REG1_M = 0x20
    CTRL_REG2_M = 0x21
    CTRL_REG3_M = 0x22
    CTRL_REG4_M = 0x23
    CTRL_REG5_M = 0x24
    STATUS_REG_M = 0x27
    OUT_X_L_M = 0x28
    OUT_X_H_M = 0x29
    OUT_Y_L_M = 0x2A
    OUT_Y_H_M = 0x2B
    OUT_Z_L_M = 0x2C
    OUT_Z_H_M = 0x2D
    INT_CFG_M = 0x30
    INT_SRC_M = 0x31
    INT_THS_L_M = 0x32
    INT_THS_H_M = 0x33


class AccelScale():
    SCALE_2G = 0
    SCALE_16G = 1
    SCALE_4G = 2
    SCALE_8G = 3

class GyroScale():
    SCALE_245DPS = 0
    SCALE_500DPS = 1
    SCALE_2000DPS = 3

class AccelODR():
    XL_PD = 0
    XL_ODR_10Hz = 1
    XL_ODR_50Hz = 2
    XL_ODR_119Hz = 3
    XL_ODR_238Hz = 4
    XL_ODR_476Hz = 5
    XL_ODR_952Hz = 6

class GyroODR():
    ODR_PD = 0
    ODR_14_9Hz = 1
    ODR_59_5Hz = 2
    ODR_119Hz = 3
    ODR_238Hz = 4
    ODR_479Hz = 5
    ODR_952Hz = 6

class AccelABW():
    ABW_408Hz = 0
    ABW_211Hz = 1
    ABW_105Hz = 2
    ABW_50Hz = 3


class MagScale():
    SCALE_4GS = 0
    SCALE_8GS = 1
    SCALE_12GS = 2
    SCALE_16GS = 3

class MagODR():
    ODR_0_625Hz = 0
    ODR_1_25Hz = 1
    ODR_2_5Hz = 2
    ODR_5Hz = 3
    ODR_10Hz = 4
    ODR_20Hz = 5
    ODR_40Hz = 6
    ODR_80Hz = 7

WHO_AM_I_AG_RSP = 0x68
WHO_AM_I_M_RSP = 0x3D

###############################################################
# coordinate vector math (x,y,z)

def cross(u, v):
    """Cross product"""
    X,Y,Z = 0,1,2
    x = u[Y] * v[Z] - u[Z] * v[Y]
    y = u[Z] * v[X] - u[X] * v[Z]
    z = u[X] * v[Y] - u[Y] * v[X]
    return (x,y,z)

def dot(u, v):
    """Dot product"""
    return sum(map(lambda s: s[0]*s[1], zip(u, v)))

def normalize(v):
    """Get a vector with a magnitude of 1 in the same direction as the given vector"""
    m = magnitude(v)
    return tuple(map(lambda n: n/m, v))

def magnitude(v):
    """Get the magnitude (length) of the given vector"""
    return sqrt(dot(v,v))


################################################################
# driver

class Axis():
    X = 0
    Y = 1
    Z = 2


class MaskDevice(I2C.Device):
    """
    An I2C device with additional functions to facilitate bitmask
    writing to registers. This is particularly useful in writing
    to device control registers.
    """

    def __init__(self, address, busnum=None, *args, **kwargs):
        if busnum is None:
            busnum = I2C.get_default_bus()
        super(MaskDevice,self).__init__(address, busnum=busnum, *args, **kwargs)

    def mask_write8(self, register, value, mask=0xFF):
        old_val = self.readU8(register)
        new_val = (old_val & ~mask) | (value & mask)
        self.write8(register, new_val)

class LSM9DS1_Magnetometer(MaskDevice):
    def __init__(self, address=0x1E, *args, **kwargs):
        super(LSM9DS1_Magnetometer,self).__init__(address, *args, **kwargs)


        # xy ultra high performance mode
        self.mask_write8(MagRegisters.CTRL_REG1_M, 0x60, mask=0x60)
        # ODR: 80Hz
        self.mask_write8(MagRegisters.CTRL_REG1_M, 0x1C, mask=0x1C)
        # fast-odr enabled (>80Hz)
        self.mask_write8(MagRegisters.CTRL_REG1_M, 0x02, mask=0x02)
        # power on, continuous conversion mode
        self.mask_write8(MagRegisters.CTRL_REG3_M, 0x00, mask=0x03)
        # z ultra high performance mode
        self.mask_write8(MagRegisters.CTRL_REG4_M, 0x0C, mask=0x0C)

        # calibration values
        self.offset = [0,0,0]

        # both the magnetometer and accelerometer raw values have kind of
        # an odd orientation on the board that doesn't really line up with
        # what the silk screen on the board indicates. Additionally,
        # they don't match with each other! This vector will be multiplied
        # with the raw read values to correct this issue.
        self.axis_correction = (-1, 1, -1)

        # between the axis correction and axis order, we can adjust our raw
        # read values to set "forward" in any orientation we want. only the
        # top level device (LSM9DS1) contains the code to set these values.
        # note, first the correction will be applied, then the axis order.
        self.axis_order = (Axis.X, Axis.Y, Axis.Z)

    def read(self):
        """Read magnetometer x, y, and z values."""
        vals = list(self.read_raw())

        # apply calibration offsets
        vals[Axis.X] += self.offset[Axis.X]
        vals[Axis.Y] += self.offset[Axis.Y]
        vals[Axis.Z] += self.offset[Axis.Z]

        order = self.axis_order

        # apply reversals as configured
        vals[Axis.X] *= self.axis_correction[Axis.X]
        vals[Axis.Y] *= self.axis_correction[Axis.Y]
        vals[Axis.Z] *= self.axis_correction[Axis.Z]

        # reorder
        vals = tuple((vals[order[Axis.X]], vals[order[Axis.Y]], vals[order[Axis.Z]]))

        return vals

    def read_raw(self):
        """
        Read raw values as reported by the sensor. This does not take into account
        axis order, offsets, or correction reversals.
        """
        raw = self.readList(MagRegisters.OUT_X_L_M, 6)
        vals = struct.unpack("<hhh", raw)
        return vals


class LSM9DS1_AccelGyro(MaskDevice):
    def __init__(self, address=0x1E, *args, **kwargs):
        super(LSM9DS1_AccelGyro,self).__init__(address, *args, **kwargs)

        # gyro ODR: 952Hz
        self.mask_write8(GyroRegisters.CTRL_REG1_G, 0xC0, mask=0xE0)
        # accel ODR: 952Hz
        self.mask_write8(GyroRegisters.CTRL_REG6_XL, 0xC0, mask=0xE0)

        # calibration values
        self.offset_accel = [0,0,0]
        self.offset_gyro = [0,0,0]

        # see: magnetometer axis_correction and axis_order
        self.axis_correction = (-1,-1,1)
        self.axis_order = (Axis.X, Axis.Y, Axis.Z)

    def read_accel(self):
        """Read accelerometer x, y, and z values."""
        vals = list(self.read_accel_raw())

        # apply calibrated offsets
        vals[Axis.X] += self.offset_accel[Axis.X]
        vals[Axis.Y] += self.offset_accel[Axis.Y]
        vals[Axis.Z] += self.offset_accel[Axis.Z]

        # correct axis direction
        vals[Axis.X] *= self.axis_correction[Axis.X]
        vals[Axis.Y] *= self.axis_correction[Axis.Y]
        vals[Axis.Z] *= self.axis_correction[Axis.Z]

        order = self.axis_order

        # reorder axes
        vals = tuple((vals[order[Axis.X]], vals[order[Axis.Y]], vals[order[Axis.Z]]))

        return vals

    def read_accel_raw(self):
        """
        Read raw accelerometer values. This does not account for axis reversal,
        calibrated offset, or axis ordering.
        """
        raw = self.readList(GyroRegisters.OUT_X_L_XL, 6)
        vals = struct.unpack("<hhh", raw)
        return vals

    def read_gyro(self):
        """Read gyroscope x, y, and z values"""
        vals = list(self.read_gyro_raw())

        # apply calibrated offsets
        vals[Axis.X] += self.offset_gyro[Axis.X]
        vals[Axis.Y] += self.offset_gyro[Axis.Y]
        vals[Axis.Z] += self.offset_gyro[Axis.Z]

        # correct axis direction
        vals[Axis.X] *= self.axis_correction[Axis.X]
        vals[Axis.Y] *= self.axis_correction[Axis.Y]
        vals[Axis.Z] *= self.axis_correction[Axis.Z]

        order = self.axis_order

        # reorder axes
        vals = tuple((vals[order[Axis.X]], vals[order[Axis.Y]], vals[order[Axis.Z]]))

        return vals

    def read_gyro_raw(self):
        """Read gyroscope values without calibration, axis reversal, or ordering applied."""
        raw = self.readList(GyroRegisters.OUT_X_L_G, 6)
        vals = struct.unpack("<hhh", raw)
        return vals

    def read(self):
        """Read accelerometer and gyroscope values"""
        return (self.read_accel(), self.read_gyro())

    def read_raw(self):
        """Read raw accelerometer and gyroscope values"""
        return (self.read_accel_raw(), self.read_gyro_raw())

class LSM9DS1:
    def __init__(self, xg_addr=0x6B, mag_addr=0x1E, axis_order=(Axis.X, Axis.Y, Axis.Z), reverse_axis=(False,False,False)):
        """
        Initialize LSM9DS1 device. note that reverse axis is applied prior to axis order, so that
        it applies to the axes as indicated on the board rather than the axes read from read_raw
        """
        self.mag = LSM9DS1_Magnetometer(mag_addr)
        self.xg = LSM9DS1_AccelGyro(xg_addr)

        mc = list(self.mag.axis_correction)
        xc = list(self.xg.axis_correction)

        if reverse_axis[Axis.X]:
            mc[Axis.X] *= -1
            xc[Axis.X] *= -1
        if reverse_axis[Axis.Y]:
            mc[Axis.Y] *= -1
            xc[Axis.Y] *= -1
        if reverse_axis[Axis.Z]:
            mc[Axis.Z] *= -1
            xc[Axis.Z] *= -1

        self.mag.axis_correction = tuple(mc)
        self.xg.axis_correction = tuple(xc)

        self.mag.axis_order = axis_order
        self.xg.axis_order = axis_order

    def read(self):
        """Read accelerometer, gyroscope, and magnetometer values"""
        mag = self.mag.read()
        accel, gyro = self.xg.read()
        return (accel, gyro, mag)

    def read_raw(self):
        """
        Read accelerometer, gyroscope, and magnetometer values
        without calibration applied. Note that axis correction is still
        performed, as reading the raw values with their axes inverted
        does not make sense.
        """
        mag = self.mag.read_raw()
        accel, gyro = self.xg.read_raw()
        return (accel, gyro, mag)

    def heading(self, mag=None, accel=None):
        """Get the magnetic heading in degrees east of north. 0 <= heding < 360"""
        if not mag:
            mag = self.mag.read()
        if not accel:
            accel = self.xg.read_accel()

        mag_norm = normalize(mag)
        accel_norm = normalize(accel)

        east = normalize(cross(mag_norm, accel_norm))
        north = normalize(cross(accel_norm, east))

        me = (1,0,0)
        a = dot(east, me)
        b = dot(north, me)

        head = atan2(a,b) * 180 / pi
        if head < 0:
            head += 360

        return 360 - head

    def pitch(self, accel=None):
        """Get the device pitch in degrees up. -90 <= pitch <= 90"""
        if accel:
            (x,y,z) = accel
        else:
            (x,y,z) = self.xg.read_accel()
        if z == 0:
            return 0

        p = atan(-x / z)
        return p * 180 / pi

    def roll(self, accel=None):
        """Get the roll of the device in degrees right of level. -180 <= roll <= 180"""
        if accel:
            (x,y,z) = accel
        else:
            (x,y,z) = self.xg.read_accel()

        if x == 0 and z == 0:
            return 0
        r = atan(y / sqrt(pow(x,2) + pow(z,2)))
        return r * 180 / pi
