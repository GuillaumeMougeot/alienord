## Instructions to setup in the car

## Instructions for drive

1. Before turning the device on:
    - Attach the camera to the top of the car looking backwards
    - The camera should be attached in an angle of 10 degrees horizontal pointing slightly to the side of the road
    - to the USB extender, plug in the GPS;
    - the hard drive;
    - the camera (blue cable of the camera). 
    - plug the device to the 12V car power outlet.
    - make sure all the cables are connected to the USB extender.
    - make sure the USB extender is plugged in the Xavier. 
    - make sure the HDMI cable is connecting the screen to the Xavier.
2. Situate the GPS close to a window, ideally hang over the rear view mirror.
3. Turn the toggle on the side of the box to 'on' and press the red button shortly to turn the device on. If started up correctly, the screen should light up. 
4. Following, a terminal window (a black window with white text) should appear indicating the pipeline has started. 
5. The desired behaviour is shown in 'Starting up & running 'as is' from local machine' subsection above. Image capture is now started and FPS (Frames Per Second) statistics are now showing.
    - The desired behaviour also includes the camera NOT fetching images if there is not enough light, if there is too much light or if the car is driving less than 80kmh to avoid image capturing in the city.
    - Troubleshooting the GPS is in the last section of the README.
6. Possible error scenarios:
    - If the error 'No input' occurs, stop the Xavier, unplug and replug the GPS from the USB extender. Restart the Xavier.
    - If the error 'No camera input', 'Getting image failed' or 'Could not find an RGB image' occurs, turn of the xavier, unplug the USB extender, unplug and replug the camera from the USB extender, replug the USB extender to the Xavier. Restart the Xavier.
7. After returning from the drive, make sure that the device has wifi connection by looking at the wifi icon in the top right corner of the screen. Providing the device has wifi connection, around 10-15 minutes after the end of the acquisition a pop-up message informing of successful transfer of images should appear. The Xavier can now be turned off.
8. In between drives, make sure that the battery is charged fully.