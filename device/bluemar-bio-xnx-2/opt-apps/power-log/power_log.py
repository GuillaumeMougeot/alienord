#!/usr/bin/env python3
"""Log the Jetson module's input rail twice a second, fsync'd after every line so the
readings from the last moments before a power loss survive it. Must run as root:
the INA3221 sysfs files are root-only. One CSV per day in /var/log/vd-power, 30 days kept."""
import datetime
import glob
import os
import time

INA = '/sys/bus/i2c/drivers/ina3221/7-0040/hwmon/hwmon2'
OUT = '/var/log/vd-power'
KEEP_DAYS = 30
PERIOD = 0.5

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ''

def sample():
    rails = [read(f'{INA}/{kind}{ch}_input') for ch in (1, 2, 3) for kind in ('in', 'curr')]
    temps = [read(f'/sys/class/thermal/thermal_zone{z}/temp') for z in (0, 1)]
    return rails + temps

def prune():
    cutoff = time.time() - KEEP_DAYS * 86400
    for path in glob.glob(f'{OUT}/power-*.csv'):
        if os.path.getmtime(path) < cutoff:
            os.remove(path)

os.makedirs(OUT, exist_ok=True)
while True:
    day = datetime.date.today()
    path = f'{OUT}/power-{day.isoformat()}.csv'
    new = not os.path.exists(path)
    prune()
    with open(path, 'a') as f:
        if new:
            f.write('time,vdd_in_mV,vdd_in_mA,cpu_gpu_mV,cpu_gpu_mA,soc_mV,soc_mA,cpu_mC,gpu_mC\n')
        while datetime.date.today() == day:
            now = datetime.datetime.now().isoformat(timespec='milliseconds')
            f.write(','.join([now] + sample()) + '\n')
            f.flush()
            os.fsync(f.fileno())
            time.sleep(PERIOD)
