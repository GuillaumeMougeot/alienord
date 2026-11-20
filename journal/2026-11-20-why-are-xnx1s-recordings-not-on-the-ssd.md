# Why are xnx1's recordings not on its SSD?

**Kind:** change · **Status:** RESOLVED (2026-11-20 10:58): the data SSD was never mounted at
`/media/data`, so the apps had written to the system disk since about January 2024. It now is (fstab),
the app writes to it, and `tools/unit-mode.sh` says READY. Step 0 of
[`tools/stock-unit-fixes.sh`](../tools/stock-unit-fixes.sh) (owner, sudo); it hung on its first run and is fixed.

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

Run by the owner at 10:52:51. Step 0 mounted the SSD (`/dev/sda1 /media/data rw,relatime`), copied the
models (11 files with the two saved engines) and the 33 recordings, kept the old folder as
`/media/data.local-20261120` (260 MB), then **hung** waiting for the app.

**Why it hung:** `systemctl stop deepstream` stopped the launch script and `docker compose`, but **not
the container**: `deepstream_app` ran on ("Up 18 hours"), never logged a new `Running...`, and still saw
the old view of `/media`. Inside it, `/media/data` was the empty root-owned folder under the new mount
(its `/media` bind is `rprivate`, so a mount made later on the host does not appear). A button press
then would have had nowhere to save. Found at 09:56 UTC; I restarted the app the no-root way
(`kill -INT`) at 09:56:56 UTC; `Running...` at 09:57:19 UTC (23 s, engines loaded from the SSD), and
the container then saw `/dev/sda1`. The script, still waiting, carried on by itself.

**A second surprise:** that restart kept the **same container ID** (`c68083774206`, "Up 16 seconds"),
whereas on 11-19 each restart made a new one. "Wait for a new container ID" (CLAUDE.md, and the script's
restart wait) is therefore not a reliable sign of a restart; a `Running...` line in the app log written
after the signal is.

**Fixed in the script:** step 0 now stops the two containers itself (`docker stop -t 30 deepstream_app
gcs`) after stopping the services; the restart wait only looks for `Running...` after the signal.

| check, 10:58 | |
|---|---|
| the app sees | `/dev/sda1 916G 30G 840G 4% /media/data`; a test file written and removed as the app's user |
| folders on the SSD | `images`, `meta`, `recordings`, `uploaded`: group `shared`, group-writable; `models`: `app:shared` |
| uploads | still off (`UPLOAD_ENABLED=False` in the gcs log after the restart) |
| LED | `Frame rate: FPS_0 (2.00) FPS_1 (3.20)`, off |
| readiness | READY FOR PRODUCTION; data disk 4 % used, 840 GB free |

Not yet seen: a boot with the new fstab line (the mount is expected before the apps start, as on
bluemar-bio-xnx-2), and a button press landing on the SSD.
