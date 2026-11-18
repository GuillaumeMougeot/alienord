# Systemd service management

Start the service
```
systemctl <APP-NAME> start
```


Check the service status
```
systemctl <APP-NAME> status
```

See the logs for the service that is running: (-f flag means "follow", so it will be live logs)
```
journalctl -fu <APP-NAME>
```

Instead, if the service didn't start, check the logs at: `/var/shared/logs/<APP-NAME>.txt`.