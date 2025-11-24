#!/usr/bin/env python3
from LSM9DS1 import LSM9DS1, Axis
import tkinter as tk
import math

def _create_circle(self, x, y, r, **kwargs):
    """Create a circle given center and radius"""
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
# monkey patch
tk.Canvas.create_circle = _create_circle

def load_calibration(imu):
    with open('calibration') as f:
        lines = f.read().splitlines()
    floats = lambda l: [float(i) for i in l]
    accel_cal = floats(lines[0].split(' '))
    gyro_cal = floats(lines[1].split(' '))
    mag_cal = floats(lines[2].split(' '))

    imu.xg.offset_accel = accel_cal
    imu.xg.offset_gyro = gyro_cal
    imu.mag.offset = mag_cal

imu = LSM9DS1(axis_order=(Axis.X, Axis.Y, Axis.Z), reverse_axis=(False, True, False))
root = tk.Tk()

class Compass:
    def __init__(self, parent, direction=0):
        self.canvas = tk.Canvas(root, \
                                width=300, \
                                height=300, \
                                borderwidth=0, \
                                highlightthickness=0, \
                                bg="black")
        self.canvas.grid()

        self.canvas.create_circle(150, 150, 120, fill="blue", outline="white")
        self.canvas.create_text(15, 15, text="Compass", fill="white", anchor="w")
        self.canvas.create_text(150,15, text="N", fill="white")
        self.canvas.create_text(15, 150, text="W", fill="white")
        self.canvas.create_text(285, 150, text="E", fill="white")
        self.canvas.create_text(150, 285, text="S", fill="white")
        self.npole = None
        self.spole = None
        self.label = None

        self.direction = 0
        self.set_direction(direction)

    def draw_magnet(self):
        if self.npole:
            self.canvas.delete(self.npole)
        if self.spole:
            self.canvas.delete(self.spole)
        if self.label:
            self.canvas.delete(self.label)

        dct = self.direction

        xtip = 120 * math.sin(math.radians(dct))
        ytip = 120 * math.cos(math.radians(dct))
        xside = 30 * math.sin(math.radians(dct + 90))
        yside = 30 * math.cos(math.radians(dct + 90))
        self.npole = self.canvas.create_polygon(\
            (150 + xtip, 150 - ytip), \
            (150 + xside, 150 - yside), \
            (150 - xside, 150 + yside),
            fill="red")
        self.spole = self.canvas.create_polygon(\
            (150 - xtip, 150 + ytip), \
            (150 + xside, 150 - yside), \
            (150 - xside, 150 + yside),
            fill="white")

        text = "{:0.4f}".format(self.direction)
        self.label = self.canvas.create_text(285, 15, \
                                             text=text, \
                                             fill="white", \
                                             anchor="e")


    def set_direction(self, direction):

        # smoothing
        ALPHA = 0.15
        diff = ((direction - self.direction + 540) % 360) - 180
        diff = 2 * ALPHA * diff # double the angle is the total diff
        self.direction = (360 + self.direction + (diff / 2)) % 360

        self.draw_magnet()

class AttitudeIndicator:
    def __init__(self, parent):
        self.canvas = tk.Canvas(root, \
                                width=300, \
                                height=300, \
                                borderwidth=0, \
                                highlightthickness=0, \
                                bg="black")
        self.canvas.grid()

        self.canvas.create_circle(150, 150, 120, fill="blue")
        self.canvas.create_text(15, 15, text="Attitude", fill="white", anchor="w")

        self.redraw = []
        self.pitch = 0
        self.roll = 0

    def draw_ground(self):
        for part in self.redraw:
            self.canvas.delete(part)

        ptext = "{:0.4f} P".format(self.pitch)
        plabel = self.canvas.create_text(285, 15, text=ptext, fill="white", anchor="e")
        rtext = "{:0.4f} R".format(self.roll)
        rlabel = self.canvas.create_text(285, 30, text=rtext, fill="white", anchor="e")

        overlay = self.canvas.create_arc(30, 30, 270, 270, style="chord", fill="green", start=180 + self.roll - self.pitch, extent=180 + (2*self.pitch))

        neutral = self.canvas.create_line(30,150,270,150, fill="grey")
        cross = self.canvas.create_line(150, 142, 150, 158, fill="grey")

        self.redraw = []
        self.redraw.append(ptext)
        self.redraw.append(plabel)
        self.redraw.append(rlabel)
        self.redraw.append(neutral)
        self.redraw.append(cross)
        self.redraw.append(overlay)

    def set_attitude(self, pitch, roll):
        # smoothing
        ALPHA = 0.3
        self.pitch = (self.pitch * (1-ALPHA)) + (pitch * ALPHA)
        self.roll = (self.roll * (1-ALPHA)) + (roll * ALPHA)
        self.draw_ground()

def update_all():
    (accel, gyro, mag) = imu.read()
    pitch = imu.pitch(accel)
    roll = imu.roll(accel)
    heading = imu.heading(mag, accel)

    compass.set_direction(heading)
    attind.set_attitude(imu.pitch(), imu.roll())
    root.after(50, update_all)

compass = Compass(root)
attind = AttitudeIndicator(root)

def main():
    load_calibration(imu)
    update_all()

    root.wm_title("Compass")
    root.mainloop()

if __name__ == '__main__':
    main()

