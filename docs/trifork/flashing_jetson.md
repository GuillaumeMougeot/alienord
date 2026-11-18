# Flashing the Xavier NX onto the external hard drive

## Preparing the flash
Pull the drivers from:

https://developer.nvidia.com/embedded/l4t/r35_release_v1.0/release/jetson_linux_r35.1.0_aarch64.tbz2 <- export the path as L4T_RELEASE_PACKAGE

https://developer.nvidia.com/embedded/l4t/r35_release_v1.0/release/tegra_linux_sample-root-filesystem_r35.1.0_aarch64.tbz2 <- export the path as SAMPLE_FS_PACKAGE


Following the steps in https://docs.nvidia.com/jetson/archives/r35.1/DeveloperGuide/text/IN/QuickStart.html:

Run:
```
tar xf ${L4T_RELEASE_PACKAGE}
cd Linux_for_Tegra/rootfs/
sudo tar xpf ../../${SAMPLE_FS_PACKAGE}
cd ..
sudo ./apply_binaries.sh
```

## Put the device in recovery mode
1. Press and hold the RECOVERY button, you'll need a needle or a pen to press it.
2. Press and hold the POWER button.
3. Release the POWER button.
4. Release the RECOVERY button.
5. Connect the device to the flashbuddy with USB, and verify that is in recovery mode using `lsusb`.

## Connect to the flashbuddy
Connect with AnyDesk with pwd: [redacted]
user: flashbuddy
password: [redacted]

BEFORE FLASHING: To avoid OEM CONFIG

https://docs.nvidia.com/jetson/archives/r35.1/DeveloperGuide/text/SD/FlashingSupport.html#skipping-oem-config

```
l4t_create_default_user.sh [-u <user>] [-p <pswd>] [-n <host>] [-a] [-h]
```
## Flashing

1. Run 

```
sudo ./nvsdkmanager_flash.sh
```

This will flash the internal eMMC card, and will allow us to boot the device.

2. On a separate window, run

```
sudo screen /dev/ttyACM0 115200
```

This will connect to the Jetson through serial port, and let you log in. If you see a black screen, try pressing Enter.
You should then see a login prompt.

3. Now we're inside the Jetson, we can check which devices are available with `lsblk`. We should see that the root partition `/` is located in the mmcblk0p1, and that there is a nvme0n1 disk available.

4. We will use fdisk to update the partitions:

    4.1 We update the `nvme0n1` disk:
    ```
    sudo fdisk /dev/nvme0n1
    ```

    Create gpt partition by using the command `g`

    Create new partition with command: `n`, choose partition 1, check the partitions with command `p`.

    Use command `w` to save and exit.

    Format the partition as ext4 with the command: 
    
    ```
    sudo mkfs.ext4 /dev/nvme0n1p1
    ```
    This only works for unmounted partitions.

    4.2 We update the `mmcblk0` disk:

    Create gpt partition by using the command `g`

    Use command `w` to save and exit.

    We should see a message saying partition 1 was not deleted because it's in use. It will be updated after boot.

5. Reboot in recovery mode:
```
sudo reboot forced-recovery
```

The `screen` command will be closed at this point.

6. Go back to the other window where we have the flash command and this time run

```
sudo ./nvsdkmanager_flash.sh --storage nvme0n1p1
```

This will flash into the nvme disk. After it finishes successfully we should try the screen command from step 2 in another window. If we get an error saying there's no `/dev/ttyACM0` device available it means the machine didn't boot up properly. Go on to the next step.

7. Try running

```
sudo /nvsdkmanager_flash.sh -r
```
The -r tells it to reuse the existing image from the first flash.

8. In another window, try again the screen command from step 2. This time we should see the login (press Enter if you only see a black screen). After logging in, we can verify the device is flashed into the nvme disk by running `lsblk`. The root partition `/` should be mounted in the `nvme0n1p1` partition.

