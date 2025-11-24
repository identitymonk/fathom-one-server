import math
from Adafruit_ADS1x15 import ADS1115


GAIN=0.000124551;
##### Temperature Monitor OBJECT CLASS ####
class TemperatureMonitor(object):
    def __init__(self, adc=None, pin=1):
        assert pin in [0,1,2,3]

        if adc is None:
            adc = ADS1115()
        self.adc = adc
        self.pin = pin # adc pin for pressure transducer

    def read_raw(self):
        global GAIN;
        """From Sensor"""
        #print(self.adc.read_adc(0))
        #print(self.adc.read_adc(0))
        #print(self.adc.read_adc(2))
        #print(self.adc.read_adc(3))

        voltage = self.adc.read_adc(0) * GAIN
        R = (16500 / voltage) - 3300
        #rinf = 0.01260797
        rinf = 0.0137107405
        den = math.log(R / rinf)
        # 4025 = BETA
        T = 4025 / den - 273.15

        #voltage2 = self.adc.read_adc(2) * GAIN
        #R2 = (16500 / voltage2) - 3300
        #den = math.log(R2 / rinf)
        #T2 = 4050 / den - 273.15

        #print(T)
        #print(T2)



        #return self.adc.read_adc(self.pin)
        return T





