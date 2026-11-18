## UPDATE APP ON EDGE

Bash based app running at boot time on the jetsons. Performs updates of the project's applications.

Modify the `config.conf` to suit your requirements. The configuration to access the Github repository needs to be done on the device.

The app needs these two files:

- `docker_apps.txt`: Simple text file with the names of the apps that are dockerized.
- `undockerized_apps.txt`: Simple text file with the names of the apps that are not dockerized.