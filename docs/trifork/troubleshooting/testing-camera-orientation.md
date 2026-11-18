# Test camera orientation

We can create a short pipeline using `gst-launch-1.0` to record a video from each camera.

## Enter the docker container

```sh
docker run -it --rm \
    --network=host \
    --runtime=nvidia \
    --hostname=docker \
    -e GST_PLUGIN_PATH=/usr/local/lib/aarch64-linux-gnu \
    --user "$(id -u app):$(id -g app)"\
    --group-add audio --group-add video --group-add i2c --group-add dialout \
    -e TERM=xterm-256color \
    -e ENV=test \
    -e DEVICE_ID=$(hostname)\
    -v /var/shared:/var/shared \
    -v /media:/media \
    -v /opt/apps/deepstream/devices:/opt/apps/deepstream/devices \
    europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base /bin/bash ;
```

## Run the pipeline with the right camera

The -e [--eos-on-shutdown] flag of the `gst-launch-1.0` command, will force the pipeline to emit an EOS before closing it. We can close with Ctrl+C after about 10 seconds.

**NOTE**: Update `<CAMERA-NAME>` with the name of the image. You can also change the `location` of the video that will be recorded (you'll need to change the path when uploading to google cloud).

```sh
gst-launch-1.0 -e aravissrc camera-name="<CAMERA-NAME>" ! capsfilter caps="video/x-bayer, format=rggb" ! bayer2rgb ! video/x-raw,format=RGBx ! videoconvert ! capsfilter caps="video/x-raw, format=I420" ! avenc_mpeg4 bitrate=1105920000 ! mpeg4videoparse ! qtmux  ! filesink location=/media/data/test-camera.mp4 sync=0 async=0
```

If image is too dark, we can change the exposure time:
```sh
arv-tool-0.8 -n "<CAMERA-NAME>" control AutoExposureTimeMax=40000
```
Then run the pipeline again. 

## Upload to GCS

```sh
gcloud storage cp /media/data/test-camera.mp4 gs://artifacts-bio
```

## Check results

If the image is blurry we should warn Develco to adjust the camera lens. **Contacts**: Develco (names and addresses kept in the private archive).