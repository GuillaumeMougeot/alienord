# Rebuilt GPU driver (`nvgpu.ko`): how it loads, how to go back

**Read this from another device if the unit will not start.** Every command is spelled out. Why
and how it was tested: [journal](../journal/2026-11-19-can-the-gpu-driver-be-fixed.md).

**Status (2026-11-19, 15:35):** installed and running (the decoder probe and Firefox leave the GPU
clock at the 510 MHz cap). To watch: the first reboot with it hung at the very end and was finished by
the watchdog (~3 min); see the journal.

## What it is

NVIDIA's GPU driver in L4T 35.1 lets its clock arbiter set the GPU to 1109 MHz, ignoring the power
mode's 510 MHz cap (+8 W, supply cut-outs). NVIDIA fixed it in L4T 35.2.1. We rebuilt the 35.1
driver with that fix for the exact kernel on the unit ([`tools/nvgpu-fix/`](../tools/nvgpu-fix/README.md)).

The original driver file is **never modified**. A loader script decides at each boot which one
to load, and falls back to the original on its own.

| file | role |
|---|---|
| `/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko` | **original** (Lenovo), untouched. sha256 `b62d7dec…3f67` |
| `/var/lib/nvgpu-fix/nvgpu-fixed.ko` | **fixed** driver. sha256 `761608e8…f3ec` |
| `/etc/modprobe.d/nvgpu-fix.conf` | one line: `install nvgpu /usr/local/sbin/nvgpu-fix-load`. **Delete it and the original loads, always** |
| `/usr/local/sbin/nvgpu-fix-load` | the loader (rules below) |
| `/etc/systemd/system/nvgpu-fix-shutdown.service` | at every clean shutdown or reboot, removes `/var/lib/nvgpu-fix/pending` |
| `/var/lib/nvgpu-fix/pending` | written before the fixed driver loads; removed at clean shutdown |
| `/var/lib/nvgpu-fix/disabled` | if present, the original loads. Written by hand, or automatically after a crash |
| `/var/lib/nvgpu-fix/boot.log` | one line per decision |
| `gpu-clock-guard.service` | stays; with the fix it has nothing to do |

The driver loads at ~6 s into boot (`systemd-modules-load`, `/etc/modules-load.d/nv.conf`), after
the NVMe root is mounted, not from the initrd: the bootloader, kernel and initrd are not involved.

## The loader's rules, at each boot

1. `disabled` exists: **original**.
2. `pending` exists (the last boot with the fixed driver did not shut down cleanly):
   - the reset reason (`/sys/devices/platform/c360000.pmc/reset_reason`) is `SYS_RESET_N`, a
     power cut or the power button: not the driver's fault; continue;
   - anything else (`MAINSWRST` after a crash, `BCCPLEXWDT` after a hang): write `disabled` with
     the reason, **original**, and it stays so until someone deletes `disabled`.
3. The fixed module's checksum is wrong, or `pending` cannot be written: **original**.
4. Otherwise: write `pending`, set `kernel.panic=10` (a crash resets the unit in 10 s instead of
   hanging until the watchdog), load the **fixed** driver; if it is refused, **original**.

So a fixed driver that crashes costs **one** crash: the unit resets itself and the next boot is on
the original. No menu, no console needed.

## Installing on another unit

Only on a Lenovo SE70 identical to bluemar-bio-xnx-2 (same Lenovo image `R35.1.0-0.0.1`, same
kernel build). From a clone of this repository (as any user with sudo), in a terminal that will not
be closed:

```bash
git clone https://github.com/GuillaumeMougeot/alienord.git ~/alienord && sudo bash ~/alienord/tools/nvgpu-fix/perm/install-nvgpu-fix.sh
```

The installer first runs [`tools/nvgpu-fix/check-same-unit.sh`](../tools/nvgpu-fix/check-same-unit.sh)
(no root needed; run it alone to just check): model, running kernel, kernel configuration, L4T
and Lenovo release, `/boot/Image`, the original `nvgpu.ko` and `nvmap.ko`, by checksum. Any
difference: nothing is installed. Then it checks the files' checksums, installs them, and offers a
reboot; the fixed driver loads from that boot on. A unit that slips past the check with a different
kernel is still safe: the kernel refuses the module and the loader loads the original.

After the reboot: `cat /sys/module/nvgpu/taint` shows `O`; `tail -2 /var/lib/nvgpu-fix/boot.log`
says `loaded the FIXED driver`. The guard (`gpu-clock-guard.service`) is not part of this
installer; with the fix it has nothing to do.

## Checking

```bash
cat /sys/module/nvgpu/taint            # "O" = fixed driver, empty = original
tail -3 /var/lib/nvgpu-fix/boot.log    # what the loader decided, and why
cat /var/lib/nvgpu-fix/disabled        # exists only if the fix is off; says why
journalctl -u gpu-clock-guard -b       # should show only "Started": the guard never had to act
```

## Going back, case by case

| case | what you do |
|---|---|
| **you want the original for a while** | `sudo touch /var/lib/nvgpu-fix/disabled && sync && sudo reboot`. Back to the fix: `sudo rm /var/lib/nvgpu-fix/disabled && sync && sudo reboot` |
| **the loader disabled the fix by itself** | read `/var/lib/nvgpu-fix/disabled` and the kernel log of the boot before (`journalctl -b -1 -k`); the unit is on the original and fine. Retry only after looking at why |
| **remove everything** | from the repository: `sudo bash tools/nvgpu-fix/perm/remove-nvgpu-fix.sh`, then reboot. By hand: `sudo rm /etc/modprobe.d/nvgpu-fix.conf && sync && sudo reboot` (the rest is then inert) |
| **unit up, but no GPU driver at all** (no desktop, no recording: a broken loader) | `Ctrl+Alt+F3` or SSH, log in, `sudo rm /etc/modprobe.d/nvgpu-fix.conf && sync && sudo reboot` |
| **crash, black screen** | wait: the unit resets itself (10 s with the fixed driver, ~4-5 min via the watchdog otherwise), and after a crash the loader switches to the original |
| **none of that works** | take the NVMe out (below) |
| **last resort** | reflash with Lenovo's SE70 image (USB recovery mode from an x86 Ubuntu PC). Recordings on the data SSD (`/media/data`) are on a separate disk |

### The NVMe on another computer

The system disk is the NVMe SSD (partition `nvme0n1p1`, ext4, label `rootfs`). On any Linux PC
with a USB NVMe enclosure (or an NVMe slot):

```bash
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL          # find the 238.5G disk; partition label "rootfs"
sudo mkdir -p /mnt/unit && sudo mount /dev/sdX1 /mnt/unit     # sdX1 = that partition
sudo rm /mnt/unit/etc/modprobe.d/nvgpu-fix.conf
sync && sudo umount /mnt/unit
```

Put the NVMe back and start the unit: it loads the original driver. Do not touch the other disk
(the 931 GB data SSD).

## Never do this

**Do not unload and reload `nvgpu` on a running system** (`rmmod` then `modprobe` or `insmod`): on
this unit it crashes the kernel, with the original driver too (11-19). Driver changes take effect
at the next boot.

Stopping the desktop (`systemctl stop gdm`) logs out every session on the unit's own screen and
keyboard, text consoles included (gdm runs `loginctl terminate-seat seat0`). Run such scripts over
SSH or under `systemd-run`.
