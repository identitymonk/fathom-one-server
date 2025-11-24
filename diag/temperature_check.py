from fathom_temperature_monitor import TemperatureMonitor
from time import sleep

temperatureMonitor = TemperatureMonitor()
# print(str(temperatureMonitor.read_raw()))
while True:
    print(temperatureMonitor.read_raw())

    sleep(5)



