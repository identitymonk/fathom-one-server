from Adafruit_ADS1x15 import ADS1115

##### Battery Monitor OBJECT CLASS ####
class BatteryMonitor(object):
    def __init__(self, adc=None, pin=3):
        assert pin in [0,1,2,3]

        if adc is None:
            adc = ADS1115()
        self.adc = adc
        self.pin = pin # adc pin for pressure transducer

    def read_raw(self):
        """From Sensor"""
        #print(self.adc.read_adc(0))
        #print(self.adc.read_adc(1))
        #print(self.adc.read_adc(2))
        #print(self.adc.read_adc(3))

        return self.adc.read_adc(self.pin)

