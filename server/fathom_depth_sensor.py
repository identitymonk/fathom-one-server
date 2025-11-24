from Adafruit_ADS1x15 import ADS1115

##### Depth Sensor OBJECT CLASS ####
class DepthSensor(object):
    MAX_PSI = 100

    def __init__(self, adc=None, pin=1):
        assert pin in [0,1,2,3]

        if adc is None:
            adc = ADS1115()
        self.adc = adc

        # XXX this changed on me while I was testing, not sure how to
        # calibrate for this. It should not change between runs
        # or with different voltages applied to the ADC+pressure transducer,
        # so long as they're receiving the same supply voltage
        self.max_raw = 22777

        self.offset = 0 # for calibration
        self.pin = pin # adc pin for pressure transducer
        self.calibrate()

    def read_raw(self):
        """From Sensor"""
        return self.adc.read_adc(self.pin)

    def read_pressure(self):
        """In PSI, raw"""
        v = self.read_raw()
        return self._psi_from_raw(v)

    def read_depth(self):
        #.43 psi / ft
        # 1.4107612 psi / m
        pdiff = self.read_pressure() - self._psi_from_raw(self.offset)
        return pdiff / .43

    def _psi_from_raw(self, raw):
        minval = .1 * self.max_raw
        maxval = .9 * self.max_raw

        # pressure transducer measures up to MAX_PSI, with
        # 1/10 input voltage at 0 and 9/10 at MAX_PSI.
        p = (raw - minval) / (maxval - minval)
        return self.MAX_PSI * p

    def read_offset(self):
        return self.offset

    def calibrate(self):
        # good to set this at "sea level" to ignore air pressure
        self.offset = self.read_raw()

