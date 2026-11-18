# Troubleshooting camera connectivity issues

We need to ensure the network switch is powered on, there should be a blue light.

If we see something like:
```
[ERROR][setup_camera]	 Error(s) setting up the camera "Daheng Imaging-MER2-231-41GC-FAA22080467":
GigEVision read_memory timeout
```

It means the camera is not reachable.

Steps to fix it:
1. Unplug the ethernet cable from the device and plug it back in.
2. Run `/opt/apps/camera/AutoIPConfigTool`.

Now the cameras should be reachable. Test it with:

```
arv-tool-0.8 -n "<NAME OF THE CAMERA>"
```

We should get a response back.