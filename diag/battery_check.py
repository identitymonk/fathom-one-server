from fathom_battery_monitor import BatteryMonitor
from time import sleep

batteryMonitor = BatteryMonitor()
print(str(batteryMonitor.read_raw()))
while True:
    batteryMonitor.read_raw()
    sleep(2)



