# gpio_blink.py
# by Scott Kildall (www.kildall.com)
# LED is on pin 4, use a 270 Ohm resistor to ground

import RPi.GPIO as GPIO
import time

p = GPIO.PWM(channel, frequency)
p.start(dc)
p.ChangeFrequency(freq)
p.ChangeDutyCycle(dc)
p.stop()


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

p = GPIO.PWM(12, 0.5)
p.start(1)
input('Press return to stop:')   # use raw_input for Python 2
p.stop()
GPIO.cleanup()

