# How the system works

The current state of unit `bluemar-bio-xnx-2`. History and reasons are in [`../journal/`](../journal/README.md).

## Hardware

| Item | Value |
|---|---|
| Compute | Lenovo ThinkEdge SE70 = NVIDIA Jetson Xavier NX; L4T R35.1.0, DeepStream 6.2, Python 3.8 |
| Disks | boot: NVMe 234 GB (`/`); data: Samsung T7 SSD 916 GB over USB (`/media/data`, by UUID in `/etc/fstab`) |
| Cameras | 2 × Daheng MER2-231-41GC GigE Vision, 1920×1200, Bayer RG8 |
| Camera network | `eth1` → switch → cameras `192.168.2.11` / `.12`; the 4G router `192.168.2.1` is DHCP server and fallback internet |
| Internet | `eth2`, office network, preferred (route metric 50); 4G via `eth1` as fallback (metric 100) |
| GPS | NMEA serial, `/dev/ttyUSB*`, 4800 baud |
| Operator box | SE70 digital I/O: **DI 1** = green button, **DO 1** = yellow LED |
| Power | one feed supplies cameras, switch and 4G router; the Jetson has its own input. See [`../journal/2026-10-23-why-does-the-unit-reset.md`](../journal/2026-10-23-why-does-the-unit-reset.md) |

**Which camera is which** is set by serial number in `/opt/apps/deepstream/devices/<hostname>.yaml`,
not by IP. **REAR** = roadkill (`…FAA22080466`, `.11`), **SIDE** = plants (`…FAA22080468`, `.12`).
The side camera is `pad_index 1` in the pipeline and the only one that button recordings capture.

## Services

| Service | Runs as | In Docker? | Job |
|---|---|---|---|
| `updates` | root | no | at boot: `git pull` from Trifork's GitHub, fetch new app packages. **Dead since Oct 2026: the token is revoked**, so it changes nothing. |
| `camera` | app | no | at boot: `AutoIPConfigTool` puts the cameras on `eth1`'s subnet |
| `deepstream` | app | yes, `deepstream_app` | the main app: both cameras → 3 detection models → saved detections and button recordings |
| `deepstream-monitoring` | monitoring | no | every 30 s: drives the yellow LED ([LED](#the-led)) |
| `gps` | app | yes, `gps` | NMEA → `/var/shared/gps-data.json` |
| `gcs` | uploader | yes, `gcs` | every 15 min: uploads `/media/data/{images,meta,recordings}` to Google Cloud, if switched on ([operations](operations.md#upload-switches)) |
| `gpu-clock-guard` | root | no | every 5 s: if the GPU clock is above the power-mode cap (after video decoding or a browser start), lowers the cap one step for a second and restores it ([journal](../journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md)) |
| `vd-power-log` | root | no | twice a second: the Jetson's input voltage and current to `/var/log/vd-power/` |
| `gcs-archive` (user) | xnx | no | one-off mirror of all cloud buckets to `/media/data/gcs-archive/`; finished 2026-11-16 |

The services talk only through files: `/var/shared/gps-data.json` (gps → deepstream),
`/var/shared/heartbeat/<app>.txt` (UNIX ms), `/var/shared/pid/deepstream.pid` (the in-container PID,
read by the button script), and `/media/data/{images,meta,recordings}` (deepstream → gcs).

**Boot order.** `updates` → `camera`, `gps`, `gcs` → `deepstream` (requires `camera`), whose launch
script starts the host-side button poller, then `docker compose up`. Inside the container `app.main`
applies camera settings with `arv-tool`, writes its PID, builds the pipeline and runs. Every service
restarts itself (`Restart=always`); a restart takes ~26 s because the AI engines are cached on the SSD.

## The pipeline

```
aravissrc REAR ─ bayer2rgb ─ nvvideoconvert ┐
                                            ├─ nvstreammux (batch 2, 1920×1080)
aravissrc SIDE ─ bayer2rgb ─ nvvideoconvert ┘
  ─ RGBA ─ nvinfer roadkill (yolov8m, FP32) ─ nvinfer car (resnet10, INT8) ─ nvinfer plant (yolov8m, FP32)
  ─ StatisticsProbe ─ RecordProbe (button recordings) ─ DumpDataProbe (detections) ─ nvdslogger ─ fakesink
```

- About **1.4 frames/s per camera**: three models on a Xavier NX. A 5 s recording is ~7 frames.
- No video output, no tracker. Frames are rescaled from 1200 to 1080 rows.

| Model | Classes | Use |
|---|---|---|
| roadkill | 10, but only `dead_animal` active (the others are disabled by a 999 threshold) | detection |
| car | 4, only `car` kept | privacy: cars are box-blurred before saving. People are detected but **not** blurred |
| plant | lupin, beach rose, parsley, parsnip, goldenrod, scotch broom, knotweed | detection |

## What gets saved

| Folder | Trigger | Conditions |
|---|---|---|
| `/media/data/recordings` | green button | none: works parked, even without GPS (filename then says `no_gps`) |
| `/media/data/images` + `meta` | automatic, per frame | fresh GPS **and speed ≥ 80 km/h**, a dead animal or plant in the frame, mean brightness 100–200 |

Filenames: `<device>_<UTC time>_<lat>N_<lon>E_c<camera>.jpg`, and `..._f<frame>_c01.jpg` for
recordings. The 80 km/h rule keeps the survey out of towns: parked or indoors, `images/` stays empty.

**The button path.** `button-push.sh` (host) polls DI 1 every 50 ms. On a press it sends `SIGUSR1` to
the app inside the container; `RecordProbe` then saves every side-camera frame for 5 s, and the
script ignores the button for 5 s. Holding the button does nothing extra in software.

## The LED

`deepstream-monitoring/launch.sh` checks every 30 s and lights the LED unless **both**:

1. the app's heartbeat is under 30 s old, and
2. the app's latest frame-rate report (in `docker logs --tail`) is under 30 s old and above zero for
   both cameras.

So **yellow = not capturing**: starting up (~1 min), crashed, cameras missing, or frozen. Green is just
power. There is no way to read the LED back; the monitor's decisions are in
`journalctl -u deepstream-monitoring`.

## The cloud side (Trifork's Google Cloud project `nordfou-biodiversity`)

Uploads go to bucket `gs://data-biodiversity/<images|meta|recordings>/<device>/`. A Cloud Function
(`bucket_finalized`) indexes every new file into a Firestore database, and a second one
(`http_query`) serves token-protected searches. The unit authenticates with the service-account key in
`/var/secrets/`. Every bucket was copied locally on 2026-11-16: [data-and-backups.md](data-and-backups.md).
