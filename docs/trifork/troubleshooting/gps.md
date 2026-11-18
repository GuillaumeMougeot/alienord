## Troubleshooting
```
NUll Island. Reinitiating
``` 
- Problem: The device is on and trying to get a fix:
- Solution: Wait; try to move the gps around; keep driving; reconnect. 

```
OSError: device reports readiness to read but returned no data (device disconnected or multiple access on port?)
```

- Problem: The port is being accessed by many processes
- Solution: ```sudo systemctl stop gps.service``` and rerun ```sudo systemctl start gps.service```.

If an empty file error occurs, it means that the GPS can't get a fix. It is set to try to get a fix automatically. If the error presists try to restart the device. 

Otherwise try restarting the device by turning the toggle to off, then on again and pressing the red button.

```
********************
Couldn't open. Reinitiating
********************
```

- Problem: The file `/dev/ttyUSB0` could not be opened.
- Solution: Check file permissions with `ls -la /dev | grep ttyUSB0`. It should have read permissions in the owner and group. Check that the gps docker container running has the group of `/dev/ttyUSB0` added in the docker compose yaml. 