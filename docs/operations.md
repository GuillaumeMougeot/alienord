# Running and debugging the unit

How-to only. Why things are this way: [`system.md`](system.md) and the [`journal`](../journal/README.md).

## Test or production? Ready to drive?

```bash
bash tools/unit-mode.sh               # status: mode, recording, cameras, GPS, GPU, disk, clock, uploads
bash tools/unit-mode.sh production    # driving settings (restarts recording once, ~1 min), then status
bash tools/unit-mode.sh test          # indoor settings, then status
```

No sudo. Ends with `READY FOR PRODUCTION` or `NOT READY` (the `FIX` lines say what). Today the
modes differ only in camera exposure (test: up to 100 ms, indoors). GPS without a fix and uploads
off are warnings, not blockers. Run it from the repository folder (`~/codes/alienord`).

## Is it working?

```bash
echo "heartbeat $(( ( $(date -u +%s%3N) - $(cat /var/shared/heartbeat/deepstream.txt) ) / 1000 )) s"  # < 30 = alive
docker logs --tail 3 deepstream_app | grep PERF        # frames per second, per camera
journalctl -u deepstream-monitoring -n 4 --no-pager    # what the LED is doing, and why
systemctl show deepstream -p NRestarts                 # restarts since boot
```

**Do not use `docker logs --since`**: it scans the whole container log (over 1 GB) and returns
nothing once a power cut has damaged it. Use `--tail`.

## Logs

| What | Where | Note |
|---|---|---|
| app logs | `/var/shared/logs/{deepstream,gps,gcs}.txt` | **UTC**, 1-2 h behind the wall clock; rotated daily, 14 kept |
| container output, FPS | `journalctl -u deepstream`, or `docker logs --tail N deepstream_app` | Docker keeps 3 × 10 MB per container |
| everything | `journalctl` (persistent since 2026-10-23) and `/var/log/syslog` | journald loses its last seconds in a power cut |
| input power | `/var/log/vd-power/power-YYYY-MM-DD.csv` | 2 samples/s, flushed to disk every line |

## Recording with the button

A short press is fine at normal load. **Keep the unit's load low**: the power supply cuts out under
sustained heavy load, which destroys anything written in the last 30 s
([journal](../journal/2026-10-23-why-does-the-unit-reset.md)). In particular, **do not run a web
browser on the Jetson**. The same recording can be started in software:

```bash
docker exec deepstream_app kill -USR1 $(cat /var/shared/pid/deepstream.pid)
```

Frames land in `/media/data/recordings/`. **Wait 30 s, or run `sync`, before the unit can lose
power**: Linux writes file contents to disk up to 30 s after the program does. The exposure is
currently set for **indoor tests** (100 ms); [revert it before driving](reverting.md#indoor-camera-exposure-2026-11-17).
Without a GPS fix, files are named `no_gps`.

## Browser and video on the unit

Fine, **as long as `gpu-clock-guard` is running** (`systemctl is-active gpu-clock-guard`). Starting
Firefox, and closing a video player that used the hardware decoder, leave the GPU clock at maximum
(+8 W, enough for the power supply to cut out after 40-70 min); the guard puts it back within ~10 s
and logs each time (`journalctl -u gpu-clock-guard`). Hardware-decoded 4K playback itself costs ~1 W.
Why: [journal](../journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md).

Still heavy: anything that decodes on the CPU (software decoders, long browsing sessions with video),
and long CPU-bound jobs; the supply is rated at ~19 W and the unit idles at ~12 W.

## Upload switches

`/opt/apps/gcs/control/upload.conf`, editable without sudo, read at the start of every 15 min cycle:

```ini
UPLOAD_ENABLED=false       # currently off: nothing is uploaded or deleted
DELETE_AFTER_UPLOAD=true   # false: after a successful upload, move files to /media/data/uploaded/<dir>/
```

Apply at once with `docker stop gcs` (systemd restarts it and it runs a cycle). Each cycle logs its
mode in `/var/shared/logs/gcs.txt`. A failed upload always keeps the file for the next cycle.

## Restarting

| What | Without sudo | With sudo |
|---|---|---|
| deepstream (also restarts the monitor) | `docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)` | `sudo systemctl restart deepstream` |
| gcs | `docker stop gcs` | `sudo systemctl restart gcs` |
| monitor only | restart deepstream | `sudo systemctl restart deepstream-monitoring` |

## Cameras and network

```bash
ip -br addr show eth1                                   # must be 192.168.2.x
ping -c1 192.168.2.11; ping -c1 192.168.2.12            # rear, side
sudo /opt/apps/camera/AutoIPConfigTool                  # rediscover cameras
journalctl -k | grep -i "link is"                       # cable or switch dropouts
```

## GPS

`cat /var/shared/gps-data.json` shows the last fix (its `timestamp` is UTC). `NUll Island` lines in `gps.txt` mean no fix. To
see raw NMEA, freeze the app so it releases the port, then read it from a throwaway container:

```bash
docker pause gps
docker run --rm --device /dev/ttyUSB0 --group-add dialout --user "$(id -u app):$(id -g app)" \
  europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base \
  python3 -c 'import serial,time; s=serial.Serial("/dev/ttyUSB0",4800,timeout=1); t=time.time()+6
while time.time()<t: print(s.readline().decode(errors="ignore").strip())'
docker unpause gps
```

`$GPGSV,1,1,00` means zero satellites in view: move the antenna to a window.

## After an unexpected reset

```bash
journalctl -k -b | grep -E "PMC reset source|REG_NVERC"   # SYS_RESET_N + 0x54/0x44 = input undervoltage; MAINSWRST + 0x0 = clean reboot
last -x | head -4                                         # "crash" = no clean shutdown
journalctl -b -1 -n 30 --no-pager                         # the last logged moments (the final seconds are lost)
tail -40 /var/log/vd-power/power-$(date -d yesterday +%F).csv /var/log/vd-power/power-$(date +%F).csv 2>/dev/null | tail -40   # voltage before the cut
ls -lt /media/data/recordings | head                      # recordings started just before it
```

Record each reset in [the reset entry](../journal/2026-10-23-why-does-the-unit-reset.md).

## The cloud mirror

`~/gcs-archive-job/status.sh` shows each bucket's files and size against its manifest.
`systemctl --user start --no-block gcs-archive` re-runs it; finished buckets are skipped.
