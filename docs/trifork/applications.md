# Applications that will be running on the device

## Main app / deepstream app
- Systemd service that runs a launcher script. It runs with the `app` user.  
- Compose yaml file that runs the deepstream application, which already includes the models and the base config. The device-specific config is mounted onto the docker container, and is available in the deploy folder of the repo.  
- A script to run the pushed button detection and forwarding the signal to the application running on the docker container.
- A launcher script that launches the script to run the pushed button first, and then launches the compose yaml.

## GPS

- Systemd service thar runs the compose yaml file. It runs with the `app` user.
- Compose yaml file that runs 1 docker container. The docker container runs a python script that updates the GPS coordinates.

## GCS / Annotation server updates
- Systemd service that runs the compose yaml file. It runs with the `uploader` user, which is part of the `gcs` group, which owns the GCS json secret.
- Compose yaml file that runs 1 docker container. The docker container runs a python script that tries to upload every 15 minutes.

## Deepstream Monitoring app
- Systemd service that runs a launcher script. It runs with the `monitoring` user, which is part of the `fleet` group, which owns the JFrog secrets.

- Launcher script that checks the heartbeat from the main app, and if it's not running, turns on a LED. This will only be possible if #17 works. In addition to this, the script checks the age of the annotations and images in disk, and if they are too old, send a warning to the Fleet backend.

## Camera configuration app
- Systemd service that runs a script.
- The script simply runs a binary file that configures the cameras

## Software monitoring app — to be created inside the `ai-core-tech-stack` repo

- Systemd service that runs the compose yaml file. It runs with the `monitoring` user, which is part of the `fleet` group, which owns the JFrog secrets.

- Compose yaml file that runs 1 docker container. The docker container runs a python script that checks the heartbeat of all the apps and send the status to the Fleet backend.

# Assumptions and agreed formats between the apps

## 1. Shared folder between different users and apps.

The shared folder on the device should be `/var/shared/` and the disk should be mounted in this location.

## 2. Location and format of the heartbeats.

The heartbeats will be located in `/var/shared/heartbeats/<name of the app>.txt` and the format will be UNIX timestamp in milliseconds.

## 3. Location and format of the gps info.

### 3.1 Location

The gps info will be located in `/var/shared/gps-data.json`.

### 3.2 Format

```json
  {
      "speed_kmh": 120.5,
      "course": 354,
      "timestamp": "20230904T145140.532" # formatted UTC timestamp with milliseconds, this is timestamp of the GPS last known location
      "latitude": {
          "degrees": 50, # integer
          "minutes": 34.4665, # float, including decimals
          "orientation": "N",
      },
      "longitude": {
          "degrees": 12, # integer
          "minutes": 56.46425, # float, including decimals
          "orientation": "E",
      },
  },
```

Note that the GPS works with the following [assumptions](./gps.md)

## 4. Location and format of the images + annotations to be uploaded to GCS.

### 4.1 Location

The location of the images and annotations to be uploaded to GCS will be `/media/data` with the following folder structure: 

```
recordings
└──<device name>_<formatted UTC timestamp>_<gps info>_f<frame number>_c<camera index>.jpg

images
└──<device name>_<formatted UTC timestamp>_<gps info>_c<camera index>.jpg

meta
└──<device name>_<formatted UTC timestamp>_<gps info>_c<camera index>.json
```

Note that the filenames of `images` and `meta` will match for annotations corresponding to a given image. **ALL** the inferenced detections will contain a GPS coordinate. This means `<gps info>` should never be empty for `images` and `meta`.

**NOTE**: The `<camera index>` format is set with a two-digit padding whereas the `<frame number>` is set with a seven-digit padding.

### 4.2 Format (json files in `meta`)

This is an example of a json annotation file:

```json
{
      "country": "Denmark",
      "device": "xnx1",
      "camera_index": 0,
      "picture_timestamp": "20230904T145200.865" # formatted UTC timestamp, when the picture was taken
      "gps": gps info, can't be null
      "objects": [ 
         ...
      ]
}
```

The format of the detected `objects` are the following:

#### For dead animals:

```json
{   ## it could include other properties like size (big/small)
    "class_label": "dead_animal",
    "display_label": "Dead Animal",
    "confidence": 0.56, # float between 0 and 1
    "model": "yolov8x_4classes_v1", # version of the model that did the detection
    "bbox_normalized": {
        "left": 0.23, # values between 0 and 1,
        "top": 0.05,
        "width": 0.15,
        "height": 0.6
    } 
}
```
#### For plants:

```json
{   ## it could include other properties
    "class_label": "plant",
    "plant_type": "lupin", # this is only for plants
    "display_label": "Lupin",
    "confidence": 0.56, # float between 0 and 1
    "model": "yolov8x_4classes_v1", # version of the model that did the detection
    "bbox_normalized": {  # maybe plants don't need this precise information
        "left": 0.23, # values between 0 and 1,
        "top": 0.05,
        "width": 0.15,
        "height": 0.6
    } 
}
```