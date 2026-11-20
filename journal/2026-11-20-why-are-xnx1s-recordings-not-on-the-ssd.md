# Why are xnx1's recordings not on its SSD?

**Kind:** change · **Status:** OPEN (2026-11-20): cause found: the data SSD was never mounted at
`/media/data`, so the apps have written to the system disk since about January 2024. Fix written
(step 0 of [`tools/stock-unit-fixes.sh`](../tools/stock-unit-fixes.sh)); waiting for the owner to run it.

Follows [bringing xnx1 up to the fixes](2026-11-19-bringing-xnx1-up-to-the-fixes.md). Times local.

## The question

The owner pressed the green button twice (08:53:28, 08:53:55) and saw nothing in the recordings folder
of the SSD shown in the file browser.

## What happened

The presses worked: the button watcher logged both, the app logged `Received start recording event!`
twice, and 33 side-camera frames (16 + 17, about 3.5 per second for 5 s) were saved, GPS-tagged, to
`/media/data/recordings/`. **That folder is on the system NVMe, not the SSD.**

| | |
|---|---|
| data SSD | `/dev/sda1`, 931.5 GB ext4, UUID `38b399e8-5d77-462b-8c6b-59d26c9e1dcc` |
| where it was | `/media/xnx/38b399e8-…dcc2`, mounted by the desktop (udisks) when someone logs in; `nosuid,nodev` |
| `/etc/fstab` | only the root line; no `/media/data` (bluemar-bio-xnx-2 has one) |
| `/media/data` | a folder on the NVMe since 2024-01-10: `images/`, `meta/` (their directory sizes show many files came and went: uploaded, then deleted), `recordings/`, and the model cache from 11-19 |
| the containers | mount `/media` (deepstream) and `/media/data` (gcs) when they start, so they see the NVMe folder, never a disk mounted later at login |
| on the SSD | 30 GB from 2023: `recordings-xnx1/` (3,304 recordings, newest 2023-10-30), `images_fullsize/` (8,347), and empty `images/`, `meta/`, `recordings/`, all group `sambashare`, which the apps (group `shared`) cannot write to. Two older empty mount folders (`…dcc`, `…dcc1`) show the desktop mounted it several times |

So in 2023 the SSD held xnx1's data, and some time around the January 2024 reinstall (most of `/opt/apps`
is dated 2024-01-10) it stopped being mounted. Nothing failed visibly: the app only checks that
`/media/data` is a directory, and the uploader deleted everything after upload anyway.

**My mistake:** on 11-19 I recorded "`/media/data` is a folder on the system NVMe, no separate data SSD"
as one of xnx1's differences, from `df`, without looking at `lsblk`. The SSD was plugged in all along.
`tools/unit-mode.sh` had the same blind spot: it reported the disk usage of whatever holds
`/media/data` as "ok". It now requires `/media/data` to be a mount point.

## The fix (step 0 of the script)

With the app and uploader stopped: unmount the desktop's mount; add
`UUID=38b3… /media/data ext4 defaults,nofail,x-systemd.device-timeout=30s 0 2` to `/etc/fstab` (`nofail`:
a missing SSD does not stop the boot); move the NVMe folder aside as `/media/data.local-20261120`; mount;
give `images/`, `meta/`, `recordings/`, `uploaded/` on the SSD to group `shared`; copy the models and the
33 recordings over; start the apps; check that the container sees `/dev/sda1` and can write to it. The
2023 data and the SSD's other folders are not touched. Tested without root: the disk detection finds
exactly `/dev/sda1` (not the NVMe, not the eMMC), and `findmnt --verify` accepts the line.

## Result

(to be filled in after the run)
