from Adafruit_ADS1x15 import ADS1115

### IMPORTANT VALUES ####
# 25535=100%
# 23463=75%
# 22693=50%
# 22278=25%
# 21983=warning
# 21785 = cutoff
#########################
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
        print("Battery: "+ str(self.adc.read_adc(3)))

        return self.adc.read_adc(self.pin)

