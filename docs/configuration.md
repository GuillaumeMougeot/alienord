# Changing the configuration

The system was not built to be tuned in the field: most values are inside container images built in
2024. There are three tiers.

## Tier A: host files, editable now

Effective after restarting the service ([operations](operations.md#restarting)). `xnx` can edit
everything under `/opt/apps/` (group `apps`). The repository mirrors these files in
[`../device/bluemar-bio-xnx-2/`](../device/README.md).

| File | Controls |
|---|---|
| `/opt/apps/deepstream/devices/<hostname>.yaml` | `COUNTRY`; which camera serial is REAR or SIDE |
| `/opt/apps/deepstream/docker-compose.yaml` | volumes: the model folder `/media/data/models` is mounted here, which is what caches the AI engines. This is also the lever for overriding Tier B |
| `/opt/apps/deepstream/button-push.sh` | button pin (`getdi 1`), polling interval (50 ms), lockout after a press (5 s) |
| `/opt/apps/deepstream-monitoring/launch.sh`, `.env` | LED logic; `HEARTBEAT_SECONDS=30` is the staleness limit and check interval |
| `/opt/apps/gcs/control/upload.conf` | upload on/off, delete-after-upload on/off |
| `/opt/apps/gcs/app-override/` | the patched upload code, mounted over the image's |
| `/etc/systemd/system/*.service` | users, restart policy (sudo) |
| `/etc/logrotate.d/vd-biodiversity` | app-log rotation (sudo) |

## Tier B: inside the images

The deepstream app's files are at `/workspaces/vd-biodiversity/bio/` in the container. To change one
without rebuilding, copy it out, edit it on the host, and mount it back:

```bash
sudo mkdir -p /opt/apps/deepstream/config-override
docker cp deepstream_app:/workspaces/vd-biodiversity/bio/configs/config.yaml /opt/apps/deepstream/config-override/
# add under volumes: in /opt/apps/deepstream/docker-compose.yaml
#   - /opt/apps/deepstream/config-override/config.yaml:/workspaces/vd-biodiversity/bio/configs/config.yaml:ro
```

`/opt/apps/deepstream/config-override/` already holds pristine, unmounted copies of the three
`pgie_*.txt`. The keys worth knowing in `configs/config.yaml`:

| Key | Value | Meaning |
|---|---|---|
| `source.cameras[*].features` | per camera | applied with `arv-tool` at every app start: resolution, frame rate, exposure and gain limits |
| `gps.GPS_SPEED_THRESHOLD` | 80 | km/h below which no detection images are saved |
| `images.BLOCK_IMAGE_MEAN_THRESHOLD_MIN/MAX` | 100 / 200 | frames outside this mean brightness are dropped |
| `recordings.RECORDING_SECONDS` | 5 | button recording length |
| `muxer.WIDTH/HEIGHT` | 1920 / 1080 | pipeline resolution |
| `heartbeat.SECONDS` | 10 | heartbeat interval; must stay well under the monitor's 30 |
| `logs.ENABLED` | true | also inserts `nvdslogger`, whose frame-rate lines the LED depends on |
| `sink.FAKESINK` | true | no video output |

Ignored or misleading: `muxer.BATCHED_PUSH_TIMEOUT_USEC` (never read; the code passes `1/FRAME_RATE`,
which rounds to 0), `images.EXCLUSION_ZONE_THRESHOLD` and `logs.VERBOSE_DUMPDATA_LOG` (never read),
`statistics.ENABLED` (not honoured).

**Detection thresholds** are in `configs/pgie_*.txt` (`pre-cluster-threshold`; lower = more
sensitive). Roadkill: only class 0, 0.1. Car: 0.3, only class `car`. Plant: per class 0.15–0.29, and
`batch-size=1` although the pipeline sends 2 frames.

The other images: `gcs` holds the upload interval (15 min), bucket and folders; `gps` holds the serial
path (`/dev/ttyUSB*`) and 4800 baud.

## Tier C: live camera settings

```bash
sudo bash scripts/arv-tool.sh -n "<camera name>" control AutoExposureTimeMax=40000   # drop the -t in the script to use it non-interactively
```

**Reverted at the next app start**, which re-applies `config.yaml`. Use it for quick experiments only.

## Camera exposure

`AutoExposureTimeMax` is in **microseconds**: 200 on the side camera (1/5000 s) and 1000 on the rear.
That freezes motion at 100 km/h in daylight, and indoors produces near-black frames that 24 dB of
gain cannot rescue. For indoor tests, raise `AutoExposureTimeMax` (Tier B, both cameras): 40000
(40 ms) or 100000 (100 ms). Revert before driving: at 80 km/h, every 10 ms is ~22 cm of motion blur.

**Currently applied (2026-11-17):** 100 ms on both cameras through `config-override/config.yaml`;
66.8/255 under a table indoors (40 ms gave 30/255). Edit that file in place, not with `sed -i`: the
container mounts this single file, and a replaced file is not seen until the container is recreated. Undo: [`reverting.md`](reverting.md#indoor-camera-exposure-2026-11-17).
