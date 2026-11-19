# Rebuilt GPU driver (`nvgpu.ko`): test, install, recover

**Read this from another device if the unit will not start.** Self-contained on purpose: every
command is spelled out. Why we do this and how the risk was weighed:
[journal](../journal/2026-11-19-can-the-gpu-driver-be-fixed.md).

**Status (2026-11-19):** building. Nothing installed. Until step 3 is done, the unit runs the
original driver and none of the recovery below is needed.

## What changes

NVIDIA's GPU driver in L4T 35.1 lets its clock arbiter set the GPU to 1109 MHz, ignoring the power
mode's 510 MHz cap (+8 W, supply cut-outs). NVIDIA fixed it in L4T 35.2.1. We rebuild the 35.1
driver with that fix added, for the exact kernel running on the unit (Lenovo's build).

| file | role |
|---|---|
| `/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko` | **original** driver (Lenovo). **Never modified.** sha256 `b62d7dec1c2b91804c909a2c18251488e83b009db88369b2e9fa4573bbc13f67` |
| `/lib/modules/5.10.104-tegra/updates/nvgpu.ko` | **fixed** driver. Does not exist until step 3 |
| `/lib/modules/5.10.104-tegra/modules.dep` | module index (`depmod`): says which file is loaded as `nvgpu`. After step 3 it points at `updates/nvgpu.ko` |
| `/opt/apps/gpu-driver-fix/` | after step 3: the fixed module's source copy, `revert.sh`, notes; root-owned |
| boot menu entry **"no GPU driver"** | after step 3: same system, kernel told never to load `nvgpu` (`module_blacklist=nvgpu`) |
| `gpu-clock-guard.service` | stays installed and running throughout; with the fix it should never act |

The driver is loaded after the root filesystem is up (`/etc/modules-load.d/nv.conf`), not from
the initrd, so the bootloader, kernel and initrd are never touched.

## The steps

1. **Build** (agent, as `xnx`, no root): changes nothing on the unit. First an *unmodified* build,
   compared with Lenovo's module; then the fixed one.
2. **Live test** (owner, one sudo script, from a text console): stop recording and the desktop,
   unload the original driver, load the fixed one from the build folder, check, then either keep
   it running until the next reboot or put the original back. **Nothing is written to
   `/lib/modules`**: any reboot returns to the original.
3. **Install** (owner, one sudo script): copy the fixed module to `updates/`, run `depmod`, place
   `revert.sh`, add the "no GPU driver" boot entry and lengthen the boot-menu wait; reboot; check.
4. **Watch**: `journalctl -u gpu-clock-guard` should stay silent even with Firefox and video.

Before step 2 or 3, switch to a **text console**: `Ctrl+Alt+F3`, log in as `xnx`. The desktop
is stopped during the live test, and terminals inside it (including tmux sessions started there)
may die.

## Recovery: what to do in each case

### The revert command

After step 3, this alone puts the original driver back (it copies the original over the fixed
copy; the index keeps pointing at `updates/nvgpu.ko`, which is now the original, so `depmod` is
not needed):

```bash
sudo cp /lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko /lib/modules/5.10.104-tegra/updates/nvgpu.ko && sync && sudo reboot
```

The same command is installed as `sudo /opt/apps/gpu-driver-fix/revert.sh`.

**Do not just delete `updates/nvgpu.ko`**: the index would still point at it, and the unit would
come up with no GPU driver at all. The tidy removal is both steps together:

```bash
sudo rm /lib/modules/5.10.104-tegra/updates/nvgpu.ko && sudo depmod -a 5.10.104-tegra && sync && sudo reboot
```

Check after the reboot that the original is loaded:

```bash
modinfo -n nvgpu        # either path is fine if the next line matches
sha256sum $(modinfo -n nvgpu)    # must be b62d7dec...3f67 (the original)
cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/cur_freq   # GPU present: a number
```

### Case by case

| case | what you see | what you do |
|---|---|---|
| **A. live test: fixed module refused** | the script says the load failed; no GPU | `sudo modprobe nvgpu` (reloads the original), then `sudo systemctl start gdm`; recording restarts by itself within a minute. Or just `sudo reboot`. Nothing was written to disk. |
| **B. live test: freeze or kernel crash** | screen frozen, or the unit reboots | reboot; hold the power button ~10 s if frozen. Nothing was written to disk; the original loads. |
| **C. installed: works but misbehaves** | errors, odd clocks, recording problems | the revert command, whenever convenient. |
| **D. installed: refused at boot** | unit boots, no desktop or a broken one, no recording | `Ctrl+Alt+F3`, log in as `xnx` (or SSH in), the revert command. |
| **E. installed: crashes at every boot** | unit reboots in a loop, or hangs during start-up | power on and watch the screen: the boot menu titled **"L4T boot options"** lists the entries; pick **"no GPU driver"** (by its number, or arrow keys and Enter). The unit starts without the GPU driver: `Ctrl+Alt+F3`, log in, the revert command, which reboots normally. |
| **F. E fails: no menu, or the entry does not help** | still looping | take the NVMe out (see below). |
| **G. last resort** | the unit will not start from any of the above | reflash with Lenovo's SE70 image (USB recovery mode from an x86 Ubuntu PC). Recordings on the data SSD (`/media/data`) are on a separate disk and are not touched by any of this. |

### F in detail: fixing the NVMe on another computer

The system disk is the NVMe SSD (partition `nvme0n1p1`, ext4, label `rootfs`). On any Linux PC
with a USB NVMe enclosure (or an NVMe slot):

```bash
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL          # find the 238.5G disk; partition label "rootfs"
sudo mkdir -p /mnt/unit && sudo mount /dev/sdX1 /mnt/unit     # sdX1 = that partition
M=/mnt/unit/lib/modules/5.10.104-tegra
sha256sum $M/kernel/drivers/gpu/nvgpu/nvgpu.ko               # must be b62d7dec...3f67
sudo cp $M/kernel/drivers/gpu/nvgpu/nvgpu.ko $M/updates/nvgpu.ko
sync && sudo umount /mnt/unit
```

Put the NVMe back and start the unit. Do not touch the other disk (the 931 GB data SSD).

## Where the boot menu lives

The kernel command line at boot does not match `/boot/extlinux/extlinux.conf` on the NVMe, so
the boot menu is most likely read from the eMMC system (`/dev/mmcblk0p1`, partition label `APP`,
not mounted). Step 3 confirms this before editing, keeps a dated backup of the file next to it,
and adds the entry there. `TIMEOUT 10` in that file is in tenths of a second (~1 s), too short to
choose; step 3 raises it. This section will be updated with what step 3 finds.
