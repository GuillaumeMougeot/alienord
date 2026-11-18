import serial
from time import sleep
from micropyGPS import MicropyGPS
from glob import glob
from app.read import ReadLine
from app.configuration import config, logger
from app.gps_handler import GpsHandler


def run_until_failure():
    try:
        my_gps = MicropyGPS()
        devices = glob(config.gps.GPS_GLOB_PATH)
        serial_port = serial.Serial(devices[0], 4800, timeout=1)
        reader = ReadLine(serial_port)
        
    except Exception as e:
        logger.error(f"""********************
                     Couldn't open. Reinitiating
                     {e}
                     ********************""")
        return
    
    gps_handler = GpsHandler(config, logger)

    while True:
        line = gps_handler.get_gps_line(reader)
        
        if line is None:
            return

        # https://community.emlid.com/t/nmea-output-string-has-changed/9515
        if 'GNRMC' in line:
            for x in line:
                my_gps.update(x)
            
            if my_gps.longitude[0] == 0 and my_gps.latitude[0] == 0: 
                # Null island in the middle of the atlantic ocean
                logger.error("""********************
                             NUll Island. Reinitiating
                             ********************""")
                return
            else:
                gps_handler.save_gps_with_timestamp(my_gps)
                gps_handler.save_heartbeat()
        
        #TODO: Test this
        # sleep(1)


if __name__ == '__main__':
    while True:
        run_until_failure()
        sleep(1)
