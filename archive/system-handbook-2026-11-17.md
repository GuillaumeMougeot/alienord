# VD Biodiversity — System Handbook

**Device examined:** `bluemar-bio-xnx-2`
**Investigation dates:** 2026-09-07 / 2026-09-08
**Audience:** the developer taking over maintenance

## 0. About this document

Everything here was derived by reading the source at `/opt/code/vd-biodiversity`, inspecting the
running containers, and reading live logs on this device. Where I state a number, it came from the
machine, not from documentation. Where something is a guess, it says so.

The original system was built by **Trifork** for a Danish Vejdirektoratet (VD) / NordFoU
biodiversity project. Trifork has discontinued it. The repo's own docs are in
`/opt/code/vd-biodiversity/docs/` and are worth reading, but they are incomplete and in places
describe intentions rather than what was shipped.

---

## 1. Hardware & platform

| Item | Value |
|---|---|
| Compute | Lenovo **ThinkEdge SE70** = NVIDIA **Jetson Xavier NX** |
| OS | L4T **R35.1.0** (JetPack 5.x), Ubuntu 20.04 |
| Runtime | **DeepStream 6.2**, GStreamer, Python **3.8.10** |
| Boot disk | `/dev/nvme0n1p1`, 234 GB |
| Data disk | `/dev/sda1`, 916 GB, mounted at `/media/data` (via `/etc/fstab` UUID entry) |
| Cameras | 2 × **Daheng Imaging MER2-231-41GC** GigE Vision, 1920×1200, Bayer RG8 |
| Camera network | `eth1` → external gigabit switch → cameras at `192.168.2.11` / `.12`; DHCP server at `192.168.2.1` |
| Internet | `eth2` (currently office LAN `10.122.85.91`); a 4G modem is also fitted |
| GPS | NMEA-over-serial on `/dev/ttyUSB*` at **4800 baud** |
| Operator I/O | SE70 digital I/O — **DI 1** = the physical button, **DO 1** = the yellow "error" LED |
| Remote access | Tailscale, on **Trifork's tailnet** `tailcfc10.ts.net` |

### Camera identity mapping

Cameras are addressed **by serial-number name**, not by IP, so IPs may change without breaking anything.
The mapping of physical position to role lives in a host file, `/opt/apps/deepstream/devices/<hostname>.yaml`:

```yaml
COUNTRY: "Denmark"
REAR_CAMERA: "Daheng Imaging-MER2-231-41GC-FAA22080466"   # 192.168.2.11 — roadkill camera
SIDE_CAMERA: "Daheng Imaging-MER2-231-41GC-FAA22080468"   # 192.168.2.12 — plant camera
```

**REAR = roadkill. SIDE = plants.** The side camera is `pad_index 1` in the pipeline, and it is the
**only** camera the button-triggered recording captures.

---

## 2. Software architecture — six systemd services

All six are enabled at boot. Three run as Docker containers, three run directly on the host.

| Service | User | Container? | What it does |
|---|---|---|---|
| `updates` | root | no | On boot: `git pull` the repo, and if anything changed, download new app tarballs from `gs://artifacts-bio` and pull new Docker images. `Type=oneshot`. |
| `camera` | app | no | Runs `AutoIPConfigTool` once — puts the GigE cameras on the same subnet as `eth1`. `Type=oneshot`. |
| `deepstream` | app | **yes** (`deepstream_app`) | The main application: reads both cameras, runs 3 detection models, saves detections and button-triggered recordings. |
| `deepstream-monitoring` | monitoring | no | Every 30 s: checks the deepstream heartbeat and drives the yellow LED. Also checks data age weekly. |
| `gps` | app | **yes** (`gps`) | Reads NMEA from serial, writes `/var/shared/gps-data.json` + a heartbeat. |
| `gcs` | uploader | **yes** (`gcs`) | Every 15 min: uploads `/media/data/{images,meta,recordings}` to Google Cloud Storage **and deletes the local copies**. |

### Inter-process contract

There is no IPC, no message bus, no database on the device. The services coordinate purely through
files in `/var/shared` and `/media/data`:

```
/var/shared/gps-data.json            gps writes  →  deepstream reads
/var/shared/heartbeat/<app>.txt      each app writes its own (UNIX ms); monitoring reads deepstream's
/var/shared/pid/deepstream.pid       deepstream writes its in-container PID; button-push.sh reads it
/var/shared/logs/<app>.txt           application logs (the real ones — see below)
/media/data/{images,meta,recordings} deepstream writes  →  gcs uploads and deletes
```

**Log locations matter.** `journalctl -u <service>` gives you container stdout (DeepStream/TensorRT
noise). The *application* log — the one with the useful Python messages — is
`/var/shared/logs/<app>.txt`. Note it is **never rotated**: `deepstream.txt` is already 3.6 MB and
`gps.txt` is 18 MB.

**Timezone trap:** the host is CEST; the containers log in **UTC**. Application logs are 2 hours
behind `journalctl` and behind the wall clock. This wastes a lot of time if you don't know it.

---

## 3. Boot & runtime sequence

```
network-online.target
  └── updates.service        (sleep 10, git pull, maybe fetch new artifacts)
        ├── camera.service            → AutoIPConfigTool, cameras get IPs
        ├── gps.service               → docker compose up (gps)
        ├── gcs.service               → docker compose up (gcs)
        └── deepstream.service        (Requires=camera.service, After=gps.service)
              └── launch-deepstream-l4t.sh
                    ├── check /media/data is present and executable
                    ├── launch-button-push.sh  → button-push.sh &   (host-side button poller)
                    └── docker compose up      → deepstream_app container
                          └── python3 -m app.main
                                ├── configure_cameras()   apply camera settings via arv-tool
                                ├── share_pid()           write in-container PID
                                └── main()                build pipeline, PLAYING, GLib main loop
```

Every service is `Restart=always` except the two `oneshot`s. If the deepstream app exits for any
reason, systemd restarts it about 1 s later — and it re-does the whole startup, including a
**~13-minute TensorRT engine build** (see Issue 1).

---

## 4. The DeepStream pipeline

Built by `bio/app/pipelines/collection.py` using a builder from Trifork's `core` package. Actual
topology on this device:

```
aravissrc(REAR) ─ capsfilter(x-bayer,rggb) ─ bayer2rgb ─ nvvideoconvert ─ capsfilter ┐
                                                                                     ├─ nvstreammux
aravissrc(SIDE) ─ capsfilter(x-bayer,rggb) ─ bayer2rgb ─ nvvideoconvert ─ capsfilter ┘   (batch=2, 1920x1080)
   │
   └─ queue ─ nvvideoconvert ─ capsfilter(RGBA)
        ─ nvinfer pgie-roadkill   (yolov8m, FP32, gie-id 1)
        ─ nvinfer pgie-car        (resnet10, INT8, gie-id 2)
        ─ nvinfer pgie-plant      (yolov8m-det, FP32, gie-id 3)
        ─ queue          ⟵ StatisticsProbe on sink pad
        ─ queue          ⟵ RecordProbe     on sink pad   (button recordings)
        ─ nvvideoconvert ⟵ DumpDataProbe   on sink pad   (detection images + json)
        ─ nvdslogger                                      (the **PERF : FPS_x** lines)
        ─ fakesink
```

Notes worth knowing:

- **`fakesink`** — there is no video output at all in production (`sink.FAKESINK: True`). The tiler
  and OSD elements exist in the builder but are never instantiated.
- **No tracker.** `configs/tracker.txt` exists and `make_tracker()` exists, but nothing calls it.
  Detections are per-frame and independent; the same animal in 3 frames is 3 unrelated detections.
- **Measured throughput is 1.41 FPS per camera** (from `nvdslogger`), against cameras configured for
  2 and 5 FPS. Three models on a Xavier NX is the bottleneck. This is why a 5-second button press
  yields ~7 frames, not 25.
- **1920×1200 → 1920×1080.** The muxer output height is 1080 while the cameras produce 1200, so
  every frame is vertically rescaled. Bounding boxes are normalised against the *muxer* dimensions.
- The three models are chained, so **each model runs on every frame** — including the car model,
  whose only purpose is privacy blurring.

### What each model is for

| Model | gie-id | Classes | Purpose |
|---|---|---|---|
| roadkill | 1 | 10: `dead_animal, car_element, sewage, shadow, road_marking, wheel, grass, obstruction, road, road_object` | Find dead animals. **Only class 0 is active** — `[class-attrs-all] pre-cluster-threshold=999` disables the rest, `[class-attrs-0]=0.1` enables `dead_animal`. |
| car | 2 | 4: `car, bicycle, person, roadsign` | **Privacy only.** `filter-out-class-ids=1;2;3` keeps only `car`; detected cars get a 200×200 box blur applied before the image is saved. |
| plant | 3 | 7: `lupin, beach_rose, parsley, parsnip, goldenrod, scotch_broom, knotweed` | Invasive/indicator plant species from the side camera. |

A frame is saved only if it contains a **dead animal or a plant** (`is_frame_interesting()`); a car
alone is not interesting, it only triggers blurring.

---

## 5. The button → recording path

This is the part you were testing. It is deliberately convoluted because the app runs inside a
container and the button is host hardware.

```
physical button  →  SE70 DI pin 1
   button-push.sh (host, user `app`, polls `./se70_tool getdi 1` every 50 ms)
      sees "DI 1: low"
      reads the in-container PID from /var/shared/pid/deepstream.pid
      docker exec <deepstream_app> kill -s SIGUSR1 <pid>
         → main.py SIGUSR1 handler publishes a START_RECORDING Gst event into the pipeline
            → RecordProbe.process_event() sets self.recording = Recording(ends = now + 5 s)
               → RecordProbe.process_batch() writes one JPEG per batch, side camera only,
                  until `ends` passes
      then sleeps 5 s (debounce)
```

Output filenames:
`<device>_<UTC timestamp>_<lat>N_<lon>E_f<7-digit frame>_c01.jpg` in `/media/data/recordings`.

Practical consequences:

- **Recording is not gated by speed.** It works parked. (Detection dumps *are* gated — see §7.)
- **Only the side camera is recorded.** `if frame.pad_index != 1: continue`.
- 5 seconds at 1.41 FPS ≈ **7 frames**. To get more frames, you need more FPS or a longer window.
- GPS is only used for the filename. No fix → the prefix becomes `no_gps`, recording still happens.
- The 50 ms polling loop costs about 5 % of a CPU core permanently. The original author left a
  comment saying this is not ideal.

---

## 6. The LED — what it actually means

`deepstream-monitoring/launch.sh`, every 30 s:

```bash
if [ $((now - heartbeat)) -lt $((HEARTBEAT_SECONDS * 1000)) ]; then
    bash set_led.sh 1 off      # → ./se70_tool doled 1 off
else
    bash set_led.sh 1 on       # → ./se70_tool doled 1 on
fi
```

**Yellow LED = "the deepstream heartbeat is more than 30 seconds old".** That is the *only* thing it
means. It is not a camera fault light, not a GPS fault light, not a disk fault light. Green is
simply power.

Two things make it noisier than it should be:

1. The heartbeat is only written once the pipeline reaches `PLAYING`. During the ~13-minute engine
   build at every start, nothing is written, so the LED is yellow the whole time — even though the
   app is healthy and working.
2. There is no distinction between "starting up" and "broken".

You can read the button (`se70_tool getdi 1`) but there is **no way to read back the LED state** —
`se70_tool` has `getdi` but no `getdo`. To know the LED state you must either look at it or trust
the monitoring log (`journalctl -u deepstream-monitoring | tail`).

---

## 7. Data — what is produced, and where it goes

### Three output streams

| Directory | Written by | Trigger | Gates |
|---|---|---|---|
| `/media/data/recordings` | `RecordProbe` | **button press** | none |
| `/media/data/images` | `DumpDataProbe` | automatic, per frame | GPS fresh (<10 s) **AND speed ≥ 80 km/h** AND frame contains animal-or-plant AND mean brightness 100–200 |
| `/media/data/meta` | `DumpDataProbe` | same as images | one JSON per image, same filename |

**This is why `images/` and `meta/` are empty in the office.** `DumpDataProbe.can_dump()`:

```python
if gps_info.speed_kmh < self.config.gps.GPS_SPEED_THRESHOLD:   # 80 km/h
    return False
```

At 0.4 km/h nothing will ever be dumped, no matter how many times you press the button — the button
does not feed that path anyway. The log states it explicitly every 150 batches:
`Driving too slow - Speed is 0.4 km/h`. The directory mtimes confirm nothing has been written there
since **2025-03-17**.

The 80 km/h threshold is a privacy/relevance rule ("don't photograph inside towns"), not a technical
limit.

### Where it goes afterwards — the answer to "where are all these images going?"

`gcs.service` runs every 15 minutes and, for each of the three directories:

```python
self.gcs.upload_blob(f, destination_blob_name)   # gcs/app/uploader.py
os.remove(f)                                     # ← local copy deleted
```

Destination:

```
gs://data-biodiversity/<images|meta|recordings>/<hostname>/<filename>
```

**The local disk is a staging buffer, not storage.** Anything you capture is gone from the device
within 15 minutes. This is why `/media/data/recordings` looked empty to you — I confirmed your three
button presses (13:39:27, 13:42:53, 13:42:59, 21 files total) were all uploaded at 13:43 and are
present in the bucket.

The bucket lives in **Google Cloud project `nordfou-biodiversity`** (project number
`1082176216244`, created 2023-07-24). The device authenticates with a service-account key at
`/var/secrets/nordfou-biodiversity-2cd0fb3af162.json`, identity
`bot-service-account@nordfou-biodiversity.iam.gserviceaccount.com`.

That key can see all buckets in the project:

```
gs://artifacts-bio/      app tarballs the device downloads on update
gs://models-bio/         model weights
gs://data-biodiversity/  ← your images, metadata and recordings
gs://data-bio/           (older data)
gs://data-roadkill/      (older data)
gs://vd-website/
gs://gcf-v2-*/           Cloud Functions sources
```

The project sits **inside a Google Cloud folder (`1038374495188`) that this service account cannot
read**, which means the project belongs to an organisation the device has no visibility into —
almost certainly Trifork's. **Establishing who legally owns that project and that data is the single
most urgent non-technical action.** See §8.

### Beyond the bucket

The `Search/` directory in the repo is the cloud half, and it still runs (or ran) in the same
project:

- A **Cloud Function** on bucket-finalize (`Search/cloud-functions/bucket-finalized`) fires for
  every uploaded file and writes a record into a **Firestore** database (the project has
  `labels: firebase: enabled`).
- A second Cloud Function (`Search/cloud-functions/query`) is a **public HTTP endpoint** serving
  searches over that database, gated by tokens generated with `Search/scripts/token_generator.py`.
- There is privacy logic in `Search/` with a `PUBLISH_THRESHOLD` and a second YOLO model
  (`yolov8n.pt`) intended to re-check images before publishing.

So the data path is: **device → Trifork's GCS bucket → Trifork's Firestore → a public query API.**
None of that infrastructure is on hardware you control.

### Bucket inventory (2026-10-23)

Links (they need a Google account with access to project `nordfou-biodiversity`; the device's key
works from the command line with `gcloud storage ls|cp gs://data-biodiversity/...`):

- Bucket: https://console.cloud.google.com/storage/browser/data-biodiversity?project=nordfou-biodiversity
- This unit's recordings: https://console.cloud.google.com/storage/browser/data-biodiversity/recordings/bluemar-bio-xnx-2?project=nordfou-biodiversity

The bucket is in `EUROPE-WEST1` (Belgium), created 2024-02-05, and **not public**: anonymous requests
get `HTTP 403`. The device key cannot read the bucket's permissions, so who else has access must come
from the project owner.

It holds the **whole fleet's** data, about **232 GB in roughly 289,000 objects**:

| Folder | Device | Files | GB |
|---|---|---|---|
| `images/` | bluemar-bio-xnx-2 | 20,215 | 15.77 |
| | bluemar-bio-xnx-3 | 5,822 | 4.94 |
| | xnx1 | 30,416 | 29.74 |
| | xnx2 | 8,517 | 5.33 |
| `meta/` | all four above | 64,962 | 0.05 |
| `recordings/` | bluemar-bio-xnx-2 | 3,208 | 2.19 |
| | bluemar-bio-xnx-3 | 49,850 | 46.93 |
| | xnx1 | 54,321 | 55.86 |
| | xnx1_rgb | 49,399 | 50.07 |
| | xnx4 | 1,986 | 4.77 |
| top level | `dataset_20241011.zip`, `dataset_20241107.zip`, `report_roadkill.csv` | 3 | 16.73 |

This unit's detection images are dated **2024-09-02 to 2024-11-01**: it has contributed no detections
since. `images/` and `meta/` should pair one-to-one, but for this unit 50 images have no metadata
file.

---

## 8. Dependency on Trifork

This is the part that should worry you, and your instinct is right. There are **seven** distinct
dependencies. Two of them are hard blockers on ever rebuilding this software.

### 8.1 Docker images — HARD BLOCKER for rebuilds, but currently safe

All three containers come from Trifork's private Artifact Registry:

```
europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base
europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gps:base
europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/gcs:base
```

The images are **already on this device** (`docker images`), so it keeps running if access is
revoked. But you cannot pull them onto a *new* device without that registry.

**Status: DONE 2026-09-08.** All three images were `docker save`d and gzip-verified — see the
change log in §14. Still needs an offsite copy.

```bash
docker save europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base \
  | gzip > /media/data/backup/deepstream-l4t-base.tar.gz
```

### 8.2 `trifork-ai-core-tech-stack` — HARD BLOCKER for source rebuilds

The application imports a package called `core` for essentially all its machinery:

```
core.infra.adapters.pipeline.pyds.driver      Driver — main loop + heartbeat
core.infra.adapters.pipeline.pyds.controller  Controller — pipeline state, bus messages
core.infra.adapters.pipeline.pyds.pipeline_builder  every GStreamer element factory
core.infra.adapters.pipeline.pyds.probes.*    BatchProbe / BatchEventProbe base classes
core.domain.*                                 BBox, Frame, Obj, Batch, events
```

It is `trifork-ai-core-tech-stack` **v0.0.1**, and `bio/requirements.txt` installs it from a private
repo at a pinned commit:

```
trifork-ai-core-tech-stack @ git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/trifork/ai-core-tech-stack@90c0b92f519beee8069d35a48e56c4fcf9969921
```

Without GitHub access to `trifork/ai-core-tech-stack` you **cannot rebuild the deepstream image from
source**. The application code in `bio/` is worthless on its own.

**The good news:** the built package is sitting in the running container and can be extracted:

```bash
docker cp deepstream_app:/usr/local/lib/python3.8/dist-packages/core /media/data/backup/core
```

**Status: DONE 2026-09-08.** 99 `.py` files plus the dist-info were extracted, and so was the
`dataclass-wizard` fork — the other private build dependency. Both are in the backup (§14). The
framework ships as plain `.py`, so you can now vendor it into your own repo and cut this dependency
permanently.

### 8.3 The GitHub repository

`/opt/code/vd-biodiversity` is a clone of `github.com/trifork/vd-biodiversity`, authenticated with a
bot token in `/var/secrets/bot.env`. `updates.service` does `git pull` on every boot.

**Update 2026-10-23: this has now happened.** At boot, `updates.service` logs
`fatal: could not read Password for 'https://ghp_…@github.com'`: GitHub rejects the token, so it has
been revoked or has expired. The update mechanism no longer works, and the 2026-09-08 bundle is now
the only copy of the repository history available to you. A side effect is that `/opt/apps` can no
longer be overwritten by an update, so the local overrides (§14) are no longer at risk from it.

Original analysis: if the repo is deleted or the token revoked, `git pull` fails. Reading `updates/update_init.sh`,
a failed pull means the output doesn't contain "Already up to date.", so it proceeds to
`git diff HEAD@{1} HEAD`, gets nothing useful, and updates nothing. **Not fatal**, but it means the
update mechanism silently stops working.

**Status: DONE 2026-09-08.** A full-history bundle was created and `git bundle verify` confirms it
"records a complete history" (§14). Note the working tree is owned by root; rather than editing your
global gitconfig, the backup was taken by copying the tree first and bundling from the copy.

### 8.4 Google Cloud project `nordfou-biodiversity` — the data question

Covered in §7. Everything the fleet has ever captured is in buckets in a GCP project inside an
organisation folder you cannot see. Also in that project: the Firestore search database, the Cloud
Functions, and the public query API.

**Actions, in order:**
1. Find out who owns GCP project `nordfou-biodiversity` — Trifork, VD, or NordFoU. The billing
   account and the org folder answer this. Ask Trifork directly and get it in writing.
2. Get an inventory and size of `gs://data-biodiversity` (and `data-bio`, `data-roadkill`).
3. Negotiate either a project transfer or a full data export to storage you control.
4. Until (1) is settled, understand that **every image this device captures is being written into
   another company's cloud account.** Whether that is acceptable is a legal/GDPR question, not a
   technical one — note that the images are of public roads and are car-blurred but not
   person-blurred (the `person` class is explicitly filtered *out* of the car model, so people are
   detected but never blurred).

The service-account key on the device is a long-lived JSON credential with broad access to that
project. **Correction (2026-10-23):** an earlier version of this handbook said that if the key were
revoked, data would pile up safely on the local disk. That was wrong. The shipped uploader swallowed
upload errors and deleted each file regardless, so a revoked key, or simply no network at upload
time, meant every captured file was **deleted without ever reaching the cloud**. This is fixed by the
uploader override in §14.4: a failed upload now leaves the file in place and retries it next cycle.

### 8.5 Model weights

`gs://models-bio/`, referenced by `bio/models/models-lock.json` with SHA-512 integrity hashes. The
weights are baked into the deepstream image already (`/workspaces/vd-biodiversity/bio/models/`), so
you have them — but back them up alongside the images (§8.1), because retraining is not realistic
without the training data, which is also in their cloud.

### 8.6 Tailscale — active remote access

This device is a node on **Trifork's tailnet** (`tailcfc10.ts.net`). `tailscale status` lists
Trifork staff machines as peers (`cgr@`, `ioka@`, `mbru@`, plus a `devicebuddy` node). Some have been
offline for 300–800 days, but the tailnet membership is live.

**This means Trifork can reach this device over the network right now.** If that is not intended,
leave the tailnet and set up your own remote access. Be aware you may be using Tailscale for your
own SSH access, so plan the cutover before pulling it.

### 8.7 JFrog Connect (fleet management)

`scripts/setup.sh` and the docs reference a JFrog Connect agent at
`/etc/connect/service/ConnectAgent` for fleet monitoring. **It is not installed on this device** —
`/etc/connect/` does not exist. One dependency you don't have to worry about. The
`deepstream-monitoring` service's stated purpose of "sending a warning to the Fleet backend" is
therefore not implemented; it only drives the LED and prints to the journal.

### Dependency summary

| Dependency | Blocks | Currently working? | Fix |
|---|---|---|---|
| `trifork-ai-core-tech-stack` | rebuilding from source | n/a (installed) | **mirrored 2026-09-08** |
| `dataclass-wizard` fork | rebuilding from source | n/a (installed) | **mirrored 2026-09-08** |
| Docker registry | new device provisioning | yes | **images saved 2026-09-08** — needs offsite copy |
| GitHub repo | updates, source history | yes | **bundled 2026-09-08** — needs offsite copy |
| GCS project / data | ownership of all captured data | yes | **legal escalation required** |
| `gs://models-bio` | retraining, new devices | yes | back up weights |
| Tailscale tailnet | remote access, and their access to you | yes | migrate to your own tailnet |
| JFrog Connect | nothing | not installed | none needed |

---

## 9. Configuration & hyperparameters — the complete map

You asked how to adjust "all these hyperparameters" generally, not just the camera. Here is the
honest answer: **the system was not designed to be tuned in the field.** Almost every meaningful
value is baked inside a Docker image built 17 months ago. There are three tiers.

### Tier A — host files you can edit right now

Effective after `sudo systemctl restart <service>`. These survive reboots. **Caveat:** they live
under `/opt/apps/`, and `updates.service` overwrites `/opt/apps/<app>/` wholesale if the Git repo
ever changes. Keep your own copies.

| File | Controls |
|---|---|
| `/opt/apps/deepstream/devices/bluemar-bio-xnx-2.yaml` | `COUNTRY`, and which physical camera is REAR vs SIDE. **Bind-mounted into the container** — the one config hook the original authors provided. |
| `/opt/apps/deepstream/docker-compose.yaml` | container user, `ENV`, `DEVICE_ID`, and **volume mounts** — this is your lever for overriding Tier B (see §9.4) |
| `/opt/apps/deepstream/button-push.sh` | DI pin number (`getdi 1`), poll interval (`sleep 0.05`), debounce (`sleep 5`) |
| `/opt/apps/deepstream/launch-deepstream-l4t.sh` | startup order, the `/media/data` precondition |
| `/opt/apps/deepstream-monitoring/.env` | `HEARTBEAT_SECONDS=30` (LED staleness threshold), `DATA_DAYS=7`, watched paths |
| `/opt/apps/deepstream-monitoring/launch.sh` | the whole LED policy — which pin, on/off logic, check interval |
| `/etc/systemd/system/*.service` | restart policy, `RestartSec`, users, start limits |
| `/opt/apps/gcs/control/upload.conf` | **upload on/off and delete-after-upload on/off** — re-read every cycle, no restart needed (§14.4) |

### Tier B — baked into the container images

Path inside the deepstream container is `/workspaces/vd-biodiversity/bio/`. To change these you
either rebuild the image (blocked, §8.2) or bind-mount an override (§9.4).

**`configs/config.yaml` — the main knob file:**

| Key | Value | Meaning |
|---|---|---|
| `PIPELINE` | `controller` | Which pipeline factory. `inference` is an unimplemented stub — do not set it. |
| `sink.FAKESINK` | `True` | No video output. Set `ONSCREEN: True` for an on-screen preview (needs a display). |
| `source.CAMERA_ON` | `True` | `False` switches to file sources from `source.files` — useful for bench testing |
| `source.cameras[0]` | REAR | `Width 1920, Height 1200, AcquisitionFrameRate 2.0, PixelFormat BayerRG8, ExposureAuto Continuous, AutoExposureTimeMax 1000, AutoExposureTimeMin 50, GainAuto Continuous, AutoGainMax 24.0, BalanceWhiteAuto Continuous` |
| `source.cameras[1]` | SIDE | as above but `AcquisitionFrameRate 5.0` and **`AutoExposureTimeMax 200`** |
| `muxer.WIDTH/HEIGHT` | 1920 / **1080** | Pipeline resolution; cameras are 1200 tall so frames are rescaled. Bounding boxes normalise against these. |
| `muxer.FRAME_RATE` | 20 | Used as `batched-push-timeout = 1/20` — **see Issue 4, this is a bug** |
| `muxer.BATCHED_PUSH_TIMEOUT_USEC` | 4000000 | **Dead value — nothing reads it** |
| `gps.GPS_SPEED_THRESHOLD` | **80** | km/h below which no detection images are saved |
| `images.SAVE_IMAGES` | `True` | Master switch for the detection-dump path |
| `images.BLOCK_IMAGE_MEAN_THRESHOLD_MIN/MAX` | 100 / 200 | Frames outside this mean-brightness band are discarded |
| `images.EXCLUSION_ZONE_THRESHOLD` | 0.2 | **Declared but never referenced in the app code** |
| `recordings.RECORDING_SECONDS` | **5** | Button recording duration |
| `heartbeat.SECONDS` | 10 | How often the app writes its heartbeat. Must stay well under monitoring's 30 s. |
| `statistics.ENABLED` | `False` | **Not honoured** — `StatisticsProbe` writes plant hits to `/var/shared/statistics.txt` regardless |
| `logs.LOG_LEVEL` | `DEBUG` | |
| `logs.ENABLED` | `True` | Double duty: file logging **and** whether `nvdslogger` (the FPS lines) is in the pipeline |
| `logs.LOG_SLOW_WAIT_FRAMES` | 150 | How often the "Driving too slow" message is printed |
| `logs.VERBOSE_DUMPDATA_LOG` | `True` | **Declared but never referenced** |

**`configs/dev.yaml`** is merged over `config.yaml` **only when `ENV=dev`**. Production runs
`ENV=test`, so dev.yaml is inert. Note the code only distinguishes `dev`; `test` and any other value
behave identically.

**`configs/pgie_*.txt` — detection thresholds** (standard DeepStream `nvinfer` config format):

| Model | Key settings |
|---|---|
| `pgie_roadkill.txt` | `network-mode=0` (FP32), `batch-size=2`, `[class-attrs-all] pre-cluster-threshold=999` (disables classes 1-9), `[class-attrs-0] pre-cluster-threshold=0.1`, `nms-iou-threshold=0.7`, `workspace-size=510` |
| `pgie_car.txt` | `network-mode=1` (INT8), `batch-size=2`, `filter-out-class-ids=1;2;3`, `pre-cluster-threshold=0.3`, `topk=20` |
| `pgie_plant.txt` | `network-mode=0` (FP32), **`batch-size=1`** (mismatched with 2 sources — see Issue 5), per-class thresholds `0.195, 0.200, 0.160, 0.290, 0.165, 0.165, 0.150`, `nms-iou-threshold=0.7` |

To make detection **more sensitive**, lower `pre-cluster-threshold`. To make it **stricter**, raise
it. To re-enable the other roadkill classes, remove the `[class-attrs-all] 999` line.

Also Tier B: the `gcs` image holds `cloud.MINUTES: 15` (upload interval), `BUCKET_NAME`, and the
list of directories to upload. The `gps` image holds `GPS_GLOB_PATH: /dev/ttyUSB*` and the 4800
baud rate (hardcoded in `app/update_gps.py`).

### Tier C — live camera registers

The cameras are GigE Vision devices with hundreds of settable features, reachable with `arv-tool-0.8`
inside the deepstream container:

```bash
# list every feature the camera exposes
sudo bash /opt/code/vd-biodiversity/scripts/arv-tool.sh -n "<CAMERA-NAME>" features

# read one
sudo bash /opt/code/vd-biodiversity/scripts/arv-tool.sh -n "<CAMERA-NAME>" control AutoExposureTimeMax

# write one
sudo bash /opt/code/vd-biodiversity/scripts/arv-tool.sh -n "<CAMERA-NAME>" control AutoExposureTimeMax=40000
```

**Critical caveat:** `bio/app/setup_cameras.py` re-applies every value from `config.yaml`'s
`source.cameras[*].features` at **every application start**. Anything you set with `arv-tool` is
silently reverted on the next restart — which, in the current broken state, is every ~13 minutes.
Tier C changes are for experiments only; to make one permanent it has to go into Tier B.

Note also that `scripts/arv-tool.sh` uses `docker run -it` and fails with
`the input device is not a TTY` in a non-interactive shell. Drop the `-t` if you script it.

### 9.4 The override recipe — how to change a Tier B value without rebuilding

This is the mechanism the system lacks and that you should add. Copy the config out of the image,
edit the copy on the host, and mount it back over the original:

```bash
# 1. extract the current configs to a host directory
sudo mkdir -p /opt/apps/deepstream/config-override
sudo docker cp deepstream_app:/workspaces/vd-biodiversity/bio/configs/config.yaml \
     /opt/apps/deepstream/config-override/config.yaml
sudo chown root:apps /opt/apps/deepstream/config-override/config.yaml

# 2. edit it — e.g. exposure, speed threshold, recording length
sudo nano /opt/apps/deepstream/config-override/config.yaml

# 3. mount it over the baked-in one: add to the `volumes:` list in
#    /opt/apps/deepstream/docker-compose.yaml
#      - /opt/apps/deepstream/config-override/config.yaml:/workspaces/vd-biodiversity/bio/configs/config.yaml:ro
#    (the same trick works for configs/pgie_*.txt)

# 4. restart
sudo systemctl restart deepstream.service
```

Two warnings: each restart costs the ~13-minute engine build until Issue 1 is fixed, and
`updates.service` may overwrite `docker-compose.yaml` — so keep this override in your own Git repo
and re-apply after any update.

---

## 10. Your specific question: the images are too dark

This is a configuration problem, not a hardware fault, and the numbers are stark.

`AutoExposureTimeMax` is in **microseconds**. The side camera is capped at **200 µs** — that is
1/5000 s. The rear camera is capped at 1000 µs (1/1000 s). These are correct for a camera bolted to
a car at 80–110 km/h in Danish daylight, where the priority is freezing motion and avoiding blur.
Indoors, under office lighting, 200 µs collects almost no light. `GainAuto` is on with
`AutoGainMax: 24.0` dB, but 24 dB of gain cannot recover 200 µs of exposure indoors.

Trifork's own troubleshooting note (`docs/troubleshooting/testing-camera-orientation.md`) says
exactly this, and suggests:

```bash
arv-tool-0.8 -n "<CAMERA-NAME>" control AutoExposureTimeMax=40000
```

**40000 µs is 200× the configured value.** That is the setting to use for indoor testing.

Recommended approach:

1. **For a quick look right now** (Tier C, reverts on restart — and the app is restarting every
   13 minutes, so be quick, or stop the service first with
   `sudo systemctl stop deepstream.service`):
   ```bash
   sudo bash /opt/code/vd-biodiversity/scripts/arv-tool.sh \
     -n "Daheng Imaging-MER2-231-41GC-FAA22080468" control AutoExposureTimeMax=40000
   ```
2. **For sustained bench work** (Tier B via §9.4): set `AutoExposureTimeMax: 40000` for both cameras
   in your override `config.yaml`. Also consider raising `AutoGainMax` to 48 if it is still dark.
3. **Before going back on the road, revert to 200 / 1000 µs.** At 80+ km/h, 40000 µs will produce
   nothing but motion blur — roughly a metre of travel per frame.

Also relevant: the detection path has its own brightness gate,
`BLOCK_IMAGE_MEAN_THRESHOLD_MIN: 100` / `MAX: 200`. Even with a good exposure, an indoor frame whose
mean pixel value falls outside 100–200 is discarded with `Image is not bright enough` / `Image is too
bright` in the log. Button recordings bypass this gate entirely, which is why your recordings exist
at all. If you want to test the *detection* path indoors, you must widen that band too.

---

## 11. Current issues, ranked

Ordered by how much they cost you. Issues 1–3 are what you are actually fighting.

### Issue 1 — Every restart costs ~13 minutes (TensorRT engines cannot be cached)

**Severity: was high. FIXED 2026-09-08 — restarts now take 26 seconds. See §14.**

TensorRT compiles each ONNX/Caffe model into a hardware-specific `.engine` file on first use and
normally caches it next to the model. Here the cache write always fails:

```
WARNING: Serialize engine failed because of file path:
  /workspaces/vd-biodiversity/bio/models/plant/model.onnx_b1_gpu0_fp32.engine opened error
0:08:37 ... failed to serialize cude engine to file: .../resnet10.caffemodel_b2_gpu0_int8.engine
```

Cause: inside the image the model directories are owned by **uid 1000**, but `docker-compose.yaml`
runs the container as `app` (**uid 116**, via `user: "${USER_ID}:${GROUP_ID}"`). No write permission,
so all three engines are rebuilt from scratch on every single start — measured at **~12–13 minutes**
(plant ≈ 7 min, car ≈ 2 min, roadkill ≈ 4 min).

Consequences, all of which you have already hit:
- The yellow LED is on for the whole 13 minutes even when nothing is wrong.
- A transient camera glitch takes the device out of service for 13 minutes per retry.
- Fixing the cable at 13:30:59 did not restore capture until 13:36:29 because a doomed build was
  already in flight.
- Any config change you make is a 13-minute test cycle.

**The trap — read this before you touch engine paths.** The obvious fix is to repoint
`model-engine-file` in the three `pgie_*.txt` at a writable directory. **It does not work.** I tried
it and measured the result: `nvinfer` uses `model-engine-file` only for *reading*. When it *builds*
an engine it derives the output path from the model file's own directory and ignores
`model-engine-file` completely. The log shows both paths at once:

```
deserialize engine from file : /media/data/engines/model.onnx_b1_gpu0_fp32.engine        <- moved
failed to serialize cude engine to file:
  /workspaces/vd-biodiversity/bio/models/plant/model.onnx_b1_gpu0_fp32.engine            <- unchanged
```

**What actually works:** make the *model directory* writable, so the read and write paths coincide
on writable storage. The models were copied out of the image to `/media/data/models` (which the
container can write, since it runs as `app:shared` and that disk is group-writable) and bind-mounted
back over `/workspaces/vd-biodiversity/bio/models`. One added line in `docker-compose.yaml`:

```yaml
      - /media/data/models:/workspaces/vd-biodiversity/bio/models
```

The `pgie_*.txt` files need **no change at all** — the original paths are correct once the directory
is writable.

Rejected alternatives: running the container as the uid that owns the model dirs (uid 1000) would
break writes to `/media/data`, because that uid is not in the `shared` group; `chown` in a rebuilt
image is blocked by §8.2.

Side benefit: the models now live on the host, so they can be inspected, swapped or updated without
rebuilding the image or touching Trifork's registry.

### Issue 2 — The GigE camera link is unstable (physical)

**Severity: high. Root cause is hardware, not software.**

**Cause confirmed by the operator:** the cable supplying **power to the cameras, the network switch
and the 4G modem** was accidentally knocked. So this was a physical disturbance, not a chronically
bad data cable — but it exposes a real design fragility (see below).

Timeline from today, after the `eth1` cable fix:

| Time | Event |
|---|---|
| 13:36:29 | pipeline PLAYING, 1.41 FPS both cameras, healthy |
| **14:02:46** | `kernel: igb eth1: NIC Link is Down` |
| **14:02:48** | `NIC Link is Up 1000 Mbps Full Duplex` — a **2-second physical link flap** |
| 14:03:05 | `Internal data stream error (-5)` on the side camera → app exits |
| 14:03:10 | restart, 13-minute engine build |
| 14:16:56 | PLAYING, then **both** cameras error within 57 ms → app exits |
| 14:17:01 | restart, engine build — LED yellow again |

A kernel-level `NIC Link is Down` is a physical-layer event, and here it was caused by the power
cable being bumped. `eth1` counters show only 325 dropped packets and 1 error over 234 GB, so the
data link itself is sound.

Historically these stream errors are rare (2025-03-19, 2026-07-01, 2026-08-28, 2026-09-07) —
roughly once per session, consistent with occasional physical disturbance rather than a failing part.

**The design fragility this exposes is the real issue.** A single power feed supplies the cameras,
the switch *and* the 4G modem. One knock therefore removes all vision and all connectivity at the
same moment — and, because of Issue 1, costs a further 13 minutes of downtime after power returns.
In a vehicle, over Danish roads, vibration and knocks are the normal operating environment. A survey
drive could lose long stretches of data to a single loose connector, and nothing on the box would
tell the driver anything beyond a yellow light that is also on during every normal start-up.

**Actions:**
1. **Add strain relief to the power connector** feeding the cameras/switch/4G, and check the switch's
   power light. This is the highest-value physical fix on the unit — a cable tie and a dab of
   retaining compound would likely prevent most field data loss.
2. Consider whether the 4G modem should be on a separate feed from the cameras, so that a camera
   power loss does not also cost you remote visibility into what went wrong.
3. Re-seat both ends of the `eth1` ↔ switch data cable too, and watch for recurrence:
   `journalctl -kf | grep -i "link is"`.
4. Fix the secondary software bug this reveals: after a power or link interruption, the **immediate**
   retry fails because the camera has not yet released its GigE stream channel (at 14:16:56 both
   cameras errored 57 ms after `PLAYING`). The app has no backoff — it just dies again and burns
   another 13-minute engine build. Once Issue 1 is fixed the retry is cheap, so add a camera-readiness
   check with a few seconds of backoff before setting the pipeline to `PLAYING`.

### Issue 3 — Startup is blind to missing cameras, and the log lies about it

**Severity: medium. This cost me and will cost you real debugging time.**

`bio/app/setup_cameras.py:15`:

```python
ERROR_MESSAGES = ['error', 'not_found', "can't connect", 'timeout']
```

`arv-tool-0.8` prints `Device 'Daheng…468' not found` — **"not found" with a space** — and exits 0.
The substring `not_found` never matches, so `setup_camera()` returns success. I verified this
directly against absent cameras: the tool printed `not found` and the app logged
`Successfully configured camera Daheng Imaging-MER2-231-41GC-FAA22080468`.

**Every "Successfully configured camera" line in the log is unconditional and meaningless.**

Compounding it, `bio/app/main.py:26-31`:

```python
for cam in config.source.cameras:
    all_ok, msg = setup_camera(cam)     # ← overwrites, should accumulate
    logger.info(f'{msg}')
if not all_ok:
    logger.error(f'{msg}')              # ← last message, not the failing one
    exit(1)
```

Only the last camera's result can ever abort startup. Fix both: `'not_found'` → `'not found'`, and
`all_ok &= ...`. Then a missing camera fails fast with a true message instead of wasting 13 minutes
building engines for a pipeline that cannot start.

### Issue 4 — The muxer batch timeout is computed wrongly

**Severity: medium — likely the reason throughput is 1.41 FPS.**

In Trifork's `core` pipeline builder:

```python
("batched-push-timeout", 1/self.config.muxer.FRAME_RATE)
```

`batched-push-timeout` is an **integer in microseconds**. With `FRAME_RATE: 20` this passes `0.05`,
which truncates to **0** — the muxer stops waiting to fill a batch. Meanwhile
`config.yaml` carries `BATCHED_PUSH_TIMEOUT_USEC: 4000000`, clearly the value someone intended, and
**nothing reads it**.

Worth an experiment once Issue 1 makes restarts cheap: this may be capping throughput well below
what the hardware can do. Fixing it means patching the extracted `core` package (§8.2).

### Issue 5 — The plant model has a batch-size mismatch

`pgie_plant.txt` sets `batch-size=1` while the muxer produces batches of 2 (one per camera). The
other two models use `batch-size=2`. nvinfer will process the batch, but less efficiently. Given the
plant engine takes the longest to build and the plant model only matters for the side camera, this
is worth revisiting.

### Issue 6 — Logs never rotate

`/var/shared/logs/deepstream.txt` is 3.6 MB, `gps.txt` is **18 MB** and growing every second (it logs
every GPS fix). No `logrotate` config exists. Add one before it becomes a problem.

**Update 2026-10-23:** worse than first stated. `logrotate` is **not installed at all**: there is no
timer, no cron job and no status file. `/var/log/syslog` (all container stdout ends up there) is
**4.0 GB** with no rotated copies, and `/var/shared/logs` is **527 MB** (`gps.txt` 354 MB,
`deepstream.txt` 172 MB). With 196 GB free this is not urgent, but nothing bounds it.

**Status 2026-10-23:** `logrotate` is installed and its daily timer is enabled, so `/var/log/syslog`
rotates from tonight (7 days kept). The app logs need their own rule, written and dry-run-validated as
`vd-biodiversity.logrotate` (daily or above 50 MB, 14 compressed rotations, `copytruncate`,
`su root shared` because the directory is group-writable). Install with
`sudo install -m 644 vd-biodiversity.logrotate /etc/logrotate.d/vd-biodiversity`. The pre-rotation
logs, the only record of the six-week outage and the 2026-10-23 resets, were archived to
`~/backup/logs-20261023/`.

### Issue 7 — The deployed code is not the repo code

The running container is `deepstream-l4t:base`, built 2024-12-13. Its
`app/pipelines/collection.py` has the **roadkill model enabled**; the repo at
`/opt/code/vd-biodiversity` has that block commented out. So the repo is *not* a reliable reference
for what is running. When you reverse-engineer behaviour, read the container:

```bash
docker exec deepstream_app cat app/pipelines/collection.py
```

### Issue 8 — Minor code defects worth knowing

- `StatisticsProbe` writes to `/var/shared/statistics.txt` on every plant detection, ignoring
  `statistics.ENABLED: False`. It also uses a `global animal_counter` that is reset per frame inside
  the loop — the "frames with at least one detection" counter is unreliable.
- `Longitude.from_dict()` returns a `Latitude` object (copy-paste bug, in both `bio` and `gps`).
  Harmless because the fields are identical, but it will bite whoever changes those classes.
- `button-push.sh`'s `kill_pid` uses `docker ps -a | grep deepstream_app`, which includes stopped
  containers. Fine today (only one match), fragile in general.
- `deepstream-monitoring/launch.sh` uses `$last_check` before it is ever set. Bash treats it as 0,
  so the data-age check runs once at startup. Benign but sloppy.
- `main.py` calls `remove_pid()` after `main()`, but `main()` blocks in the GLib loop and the process
  is usually killed — so the stale PID file is normal, not a symptom.

### Issue 9 — Live credentials are world-readable on the device

**Severity: medium-high. Found while taking the backups.**

Two long-lived credentials sit on the device with mode `-rw-r--r--`, readable by every account:

| File | Contents | Grants |
|---|---|---|
| `/var/secrets/bot.env` | `GITHUB_TOKEN=ghp_…` in plaintext | access to Trifork's private GitHub repos |
| `/opt/code/vd-biodiversity/.git/config` | the **same token embedded in the remote URL** | as above |
| `/var/secrets/nordfou-biodiversity-2cd0fb3af162.json` | GCP service-account private key | read/write on every bucket in project `nordfou-biodiversity`, i.e. all fleet imagery ever collected |

`setup-xnx.sh` also sets `git config --global credential.helper store`, so the token is likely
duplicated in `/root/.git-credentials`.

Note the asymmetry: the GCS key was at least given a restricted group (`uploader:gcs`) by
`setup-xnx.sh`'s `permissions()` function, but the mode is still `644`, which defeats it.

**Actions:**
1. Copy both credentials into a password manager. Do **not** put them in backup archives — the
   backup taken on 2026-09-08 deliberately excludes them and has the token stripped from the
   worktree copy's `.git/config`.
2. `chmod 640` both, with the correct owning group.
3. Once you have finished mirroring anything you need from Trifork's GitHub, ask them to **rotate the
   GitHub token**. The 2026-09-08 backup already contains the full `vd-biodiversity` history and both
   private build dependencies, so nothing further should be needed from their GitHub.
4. Treat the GCS key as the thing that controls access to your data. If Trifork rotates it, uploads
   fail and `gcs.service` logs `Couldn't upload … to GCS`. With the §14.4 override in place the files
   then stay on the 916 GB disk for retry; without it they would be silently deleted.

### Issue 9b — Credentials in Trifork's Git history (found 2026-11-16)

Deleted from the files later, but still in old commits: the **live** Google Cloud key (same key ID as
`/var/secrets/…json`, commit 9274ed3, branch `jwme/refactor_makefile`), a GitHub token
(`secrets/.env`, same branch), and a cloud-search database key (`Search/infra/BioDiversityService/
cloudfire-biodiversity.json`, in `main`'s history). The current `docs/flashing_jetson.md` also holds
what looks like a real 6-character device password. Consequences: the bucket key has been readable by
anyone with access to Trifork's GitHub since August 2023 and should be rotated; and the history must be
rewritten, or replaced with a fresh one, before the repository gets any remote. Details and options are
in the handover repository's `handover/README.md`.

### Issue 10 — The unit's power supply collapses (resets with and without the button)

**Update 2026-10-23, 15:28: a third reset with no button press and nobody touching the unit.** The
journal (persistent since 14:46) shows normal operation right up to 15:28:29.76, then nothing.

**Cause, from the PMIC's event recorder.** At every boot the kernel prints
`max77620-power max20024-power: Event recorder REG_NVERC : 0x..`, the power-management chip's
non-volatile record of why the board last lost power. In the MAX77620/MAX20024 bit layout (bit 7
reset input, 6 input undervoltage lockout, 5 input overvoltage, 4 input low, 3 thermal overload,
2 hard reset, 1 watchdog, 0 shutdown pin):

| Value | Meaning | Seen at |
|---|---|---|
| `0x54` | input undervoltage lockout + input low + hard reset | every `SYS_RESET_N` boot since Sep 2024, including all three resets on 2026-10-23 |
| `0x44` | input undervoltage lockout + hard reset | 2025-03-03, 2026-07-01, 2026-08-28 |
| `0x0` | nothing: clean | every software reboot (`MAINSWRST`), e.g. 2026-10-23 13:48 |

So these resets are **the supply voltage to the module collapsing**, not software, heat or a
watchdog. The register can't tell a deliberate power-off from a failure, so a reset counts as a fault
only when nobody switched the unit off; the 15:28 one qualifies.

**Baseline when healthy:** module input 4.95–4.96 V, 2.3–2.9 A (~11.8 W), steady; SoC 50–56 °C.

**Next steps (physical):** check the DC supply and its rating against the total load (Jetson, two
cameras, switch, 4G router, USB disk); check every connector and terminal in the power path; try a
known-good supply. Install the input-rail logger so the next collapse is recorded:
`sudo cp /opt/apps/power-log/vd-power-log.service /etc/systemd/system/ && sudo systemctl enable --now vd-power-log`.
It writes `/var/log/vd-power/power-YYYY-MM-DD.csv` twice a second, fsync'd. After a reset, the last
lines show whether the 5 V rail sagged first (weak or overloaded supply) or held to the end (abrupt
disconnection). Caveat: the INA3221 measures the module's 5 V rail after the carrier's regulator, so
measuring the box's DC input directly is still the definitive test.

**Correction 2026-11-17: every button press on 23 Oct was followed by a reset.** A third press, at
16:18:56, is proven by its recording files in `/media/data/recordings/`. The journal missed it
because its last ~20 s were lost in the power cut, like the others. So on 23 Oct: presses at
13:27:57, 14:19:16 and 16:18:56, each followed by a reset within ~30 s (3 of 3). Resets without a
press: 15:28 and 16:32 (and 16:44 and 26 Oct 17:11, which may have been deliberate power-offs). On
8 Sep, by contrast, seven presses caused no reset. Two conclusions: the power path is marginal on its
own, and since September the button reliably tips it over. **Inspect the button box and its wiring
first.**

Recordings and their fate (all of 2026):

| When (local) | Where | Frames | State |
|---|---|---|---|
| 8 Sep, 7 button presses + 1 software test | cloud mirror, `gcs-archive/data-biodiversity/recordings/bluemar-bio-xnx-2/` | 59 | all valid, GPS-tagged |
| 23 Oct 13:27:57 | cloud mirror | 7 | 6 empty, frame 0 truncated (no JPEG end marker) |
| 23 Oct 14:19:16 | `/media/data/recordings/` | 16 | 15 empty, 1 truncated |
| 23 Oct 16:18:56 | `/media/data/recordings/` | 16 | 12 empty, 4 truncated |

Every 23 Oct recording was destroyed by the power cut that followed it: the frames were written to
the disk cache but never flushed.

The original analysis follows.

#### Original analysis: pressing the button hard-resets the unit

**Severity: high. Found 2026-10-23.**

Both button presses on 2026-10-23 were followed, about 5 seconds later, by an abrupt power-loss reset:

| Press | Last line that reached syslog | Next boot | Reset source |
|---|---|---|---|
| 13:27:57 | 13:28:00, then null bytes | 13:30:36 | `SYS_RESET_N` |
| 14:19:16 | 14:18:51 (buffer lost; frames run to 14:19:21) | 14:20:01 | `SYS_RESET_N` |

How to read the evidence:
- `SYS_RESET_N` is the external reset line. It is what every plain power-on records. A `reboot`
  records `MAINSWRST`; a watchdog or thermal trip records its own source. `last -x` shows the
  previous session ending in `crash`, with no shutdown record.
- The kernel logged no panic, over-current, under-voltage or thermal warning.
- The recordings show the damage: of the 7 frames from 13:27:57, frames 1–6 are **0 bytes** and
  frame 0 is truncated (an earlier version of this note wrongly called it intact). The original uploader then put those empty files in the bucket. Of the 16 frames
  from 14:19:16, 15 are 0 bytes and the 16th ends in null bytes.
- On **2026-09-08, eight presses caused no reset at all**, and software-triggered recordings
  (`SIGUSR1`, same code path) were fine. So the change is in the button hardware or how it is
  pressed, not in the recording software.
- The unit stays up for ~5 s after the press. That rules out an immediate short at the moment of
  pressing.

**Leading hypothesis (unconfirmed):** the button is wired to, or shorts onto, the SE70's remote
power-switch input as well as DI 1. A ~5 s hold is the classic forced-power-off duration. Test it:
a quick tap (< 1 s) versus a deliberate 5 s hold. If only the hold resets the unit, inspect the
button box wiring. Until then, **tap the button briefly**.

The crash during the 2026-10-23 inspection was this: the 14:19:16 press, not the gcs restart that
happened 25 s earlier.

### Issue 11 — The LED was blind to a six-week crash loop (regression from the Issue 1 fix)

**Severity: was high (caused by the 2026-09-08 engine-cache fix). FIXED 2026-10-23 — see §14.5.**

The heartbeat is written once each time the app reaches `Running...`, even if it dies 10 ms later.
Before the Issue 1 fix, each crash cost 13 minutes, so the heartbeat went stale and the LED was
yellow. After the fix, a crash-and-restart cycle takes ~30 s. During the 8 Sep–20 Oct crash loop the
gap between heartbeats was a median **31 s** (p90 38 s) against the 30 s threshold, so **the LED
was yellow only 8.1% of the time**. For six weeks the unit captured nothing while its fault lamp
mostly said it was fine.

The root problem is that the heartbeat means "the process started", not "frames are flowing". The
LED now also requires a recent, non-zero frame rate for every camera (§14.5).

### Issue 12 — Six weeks without capture, 8 Sep–20 Oct 2026

**Severity: high (outcome); cause unknown.**

The last healthy run ended on 2026-09-08 at 17:28 local time with `Internal data stream error (-5)`,
the same signature as a camera power or link loss. From then until the unit was switched off on
20 Oct, discovery never found the cameras again: **118,431 starts**, each failing with
`Could not find camera …468`, ~2,500–3,700 per day. GPS kept working throughout, so the Jetson was
up and only the camera side (cameras, switch and 4G on one power feed) was gone. Powering everything
on again on 2026-10-23 brought the cameras straight back.

Why the camera side stayed down cannot be established: journald was **volatile**, so the network and
link history from those weeks was lost at the next boot.

**Done 2026-10-23:** the journal is now persistent (`/var/log/journal`). One follow-up is needed: the
directory was created without the standard permissions, so members of `adm` (including `xnx`) can no
longer read it, and `journalctl -u …` returns `-- No entries --`. Fix:
`sudo systemd-tmpfiles --create --prefix /var/log/journal`. Until then, the same messages are in
`/var/log/syslog`.

### Issue 13 — GPS has no sky view

The receiver works: its clock and date are correct. But raw NMEA shows `$GPGSV,1,1,00` (zero
satellites in view) and fix quality 0. It had fixes in the same office on 8 Sep and 20 Oct, so the
antenna has most likely moved away from a window. Effects: recordings are tagged `no_gps`, detection
dumps are impossible, and `gps.txt` grows by three `NUll Island` lines every 2 s.

To read raw NMEA without fighting the GPS app for the port, freeze it for a few seconds:
`docker pause gps`, read `/dev/ttyUSB0` from a throwaway container, then `docker unpause gps`.

### Current state as of the end of this investigation

- Cameras reachable, network correct: `eth1` = `192.168.2.126` (cameras), `eth2` = office LAN.
- The button/recording path is **proven working** — 3 presses, 21 JPEGs, all uploaded to GCS.
- GPS working, fix at 56.165 N 10.205 E.
- `deepstream.service` has restarted **106 times**; it is currently in an engine build following the
  14:16:56 camera dropout, so the yellow LED is on. It should clear about 13 minutes after each
  restart and stay clear until the next link flap.

---

## 12. Diagnostic cookbook

```bash
# --- is the main app actually alive? (this is what the LED reflects) ---
echo $(( ( $(date -u +%s%3N) - $(cat /var/shared/heartbeat/deepstream.txt) ) / 1000 ))  # seconds stale
# < 30 = healthy. Larger = LED is yellow.

# --- application logs (UTC! two hours behind the host clock) ---
tail -f /var/shared/logs/deepstream.txt
tail -f /var/shared/logs/gps.txt
tail -f /var/shared/logs/gcs.txt

# --- container stdout: TensorRT, GStreamer, FPS ---
journalctl -u deepstream.service -f
journalctl -u deepstream.service | grep "PERF"        # effective FPS per camera

# --- LED decisions, live ---
journalctl -u deepstream-monitoring.service -f

# --- restart count and current uptime ---
systemctl show deepstream.service -p NRestarts -p ActiveEnterTimestamp

# --- are the cameras on the network? ---
ping -c2 192.168.2.11 && ping -c2 192.168.2.12
ip -br addr show eth1                                  # MUST be 192.168.2.x
sudo /opt/apps/camera/AutoIPConfigTool                 # re-run discovery; lists cameras
docker run --rm --network=host \
  europe-west1-docker.pkg.dev/nordfou-biodiversity/docker-registry-bio/deepstream-l4t:base \
  arv-tool-0.8                                         # enumerate GigE devices

# --- physical link flaps (Issue 2) ---
journalctl -kf | grep -i "link is"
ip -s link show eth1                                   # errors / dropped counters

# --- the button ---
/opt/apps/deepstream/se70_tool getdi 1                 # "high" = released, "low" = pressed
/opt/apps/deepstream/se70_tool dicounter 1             # count presses interactively
ps -ef | grep button-push                              # the poller must be running

# --- the LED (write-only; there is no read-back) ---
/opt/apps/deepstream-monitoring/se70_tool doled 1 on
/opt/apps/deepstream-monitoring/se70_tool doled 1 off

# --- did my recording land? (local copy is deleted within 15 min) ---
ls -la /media/data/recordings/
grep "Received start recording event" /var/shared/logs/deepstream.txt
gcloud storage ls gs://data-biodiversity/recordings/$(hostname)/ | tail

# --- why are images/meta empty? ---
grep -E "Driving too slow|not bright|too bright|GPS is not available" \
  /var/shared/logs/deepstream.txt | tail

# --- what code is actually running? ---
docker exec deepstream_app cat app/pipelines/collection.py
docker exec deepstream_app cat configs/config.yaml
docker exec deepstream_app pip3 show trifork-ai-core-tech-stack
```

---

## 13. Suggested remediation roadmap

**Do this week — irreversibility risk**

1. Extract Trifork's `core` package out of the container and into your own Git repo (§8.2). Without
   it you can never rebuild. Thirty seconds of work.
2. `docker save` all three images to the data disk and offsite (§8.1).
3. Mirror the GitHub repo (`git bundle`) while the bot token still works (§8.3).
4. Back up the model weights.
5. Open the ownership question on GCP project `nordfou-biodiversity` in writing (§8.4). This is the
   long-lead item — start the clock now.

**Then — make the system debuggable**

6. Fix the engine cache (Issue 1). Restarts go from 13 min to ~20 s. Everything else gets easier.
7. Fix the two `setup_cameras.py` / `main.py` defects (Issue 3) so the logs stop lying.
8. Add the config-override bind mount (§9.4) so you can tune without rebuilding.
9. Add logrotate (Issue 6).

**Then — make it reliable**

10. Chase the physical link flap (Issue 2): re-seat, swap cable, check the switch.
11. Add a camera-readiness check with backoff before the pipeline starts, instead of exit-and-retry.
12. Make the LED distinguish "starting up" from "broken" — for instance a slow blink during the
    engine build. Right now an operator cannot tell a booting device from a dead one.
13. Experiment with the muxer batch timeout (Issue 4) to see whether throughput improves.

**Then — decide the future**

14. Migrate off Trifork's tailnet to your own remote access (§8.6).
15. Decide whether to keep the cloud pipeline (their GCS + Firestore + public query API) or
    repoint `gcs.service` at your own bucket. Repointing is a one-line change to
    `cloud.BUCKET_NAME` plus your own service-account key — genuinely easy, and it stops new data
    flowing into someone else's account. This may be the fastest way to de-risk the data question
    while the ownership discussion runs.


---

## 14. Change log — 2026-09-08

Two pieces of work were carried out on the device. Both are reversible and both are recorded here so
a future maintainer can see what differs from the as-shipped system.

### 14.1 Recovery backup taken

Contents and restore instructions are in the backup's own `README.md`. Two copies exist:

```
~/backup/vd-biodiversity-20260908/                  (boot disk, staging)
/media/data/backup/vd-biodiversity-20260908/        (data disk, root:shared)
```

Both verified byte-identical at **4,331,426,154 bytes**. Contents: Trifork's `core` framework
(99 `.py` files) and the `dataclass-wizard` fork — the two hard blockers on rebuilding; the three
container images (`gzip -t` clean, valid `manifest.json` each); the model weights; a full-history
Git bundle (`bundle verify`: "records a complete history"); `/opt/apps` including the `se70_tool`
and `AutoIPConfigTool` vendor binaries; the systemd units and network config.

**No credentials were included.** The GitHub token was stripped from the worktree copy's
`.git/config`. See Issue 9.

**Still outstanding: an offsite copy.** Both copies are on the machine they protect, so this is not
yet a backup in any meaningful sense. `/media/data` needs root to write, so this step needs your
credentials:

```bash
tar -czf vd-biodiversity-backup-20260908.tar.gz -C /media/data/backup vd-biodiversity-20260908
rsync -avP vd-biodiversity-backup-20260908.tar.gz <your-offsite-target>
```

### 14.2 Engine cache fixed — restarts 13 min → 26 s

| Measurement | Before | After |
|---|---|---|
| Cold start (engines built) | ~792 s | ~792 s (once only) |
| **Restart (engines cached)** | **~792 s, every time** | **26 s** |
| `failed to serialize` in log | every start | gone |

Changes made, all on the host:

1. `/media/data/models` — models copied out of the image by the container itself (verified
   byte-identical, 202,682,807 bytes / 12 files), owned `app:shared`.
2. `/opt/apps/deepstream/docker-compose.yaml` — one line added mounting that directory over the
   image's models path. Original preserved as `docker-compose.yaml.orig-20260908`.
3. `/opt/apps/deepstream/config-override/` — pristine copies of the three `pgie_*.txt`, **not
   mounted**. Left in place as a ready-made scaffold for the override recipe in §9.4.

Verified afterwards: engines persist (`plant` 129 MB, `roadkill` 148 MB, `car` 1.9 MB); a subsequent
restart deserialized all three from cache and reached `Running...` in 26 s; pipeline steady at
1.40 FPS; heartbeat fresh and the LED off; and an end-to-end recording test (the same `SIGUSR1` the
button sends) produced 8 GPS-tagged JPEGs, confirming the mount change did not disturb the capture
path.

**To revert:** restore `docker-compose.yaml.orig-20260908` and restart. The device then reads models
from inside the image again and returns to 13-minute restarts.

**Warning:** `updates.service` replaces `/opt/apps/<app>/` wholesale whenever the Git repo changes,
which would silently drop the compose mount and put you back to 13-minute restarts. Keep the patched
compose file in your own repo and re-apply after any update. Note that `/media/data/models` itself
would survive — only the mount line is lost.

### 14.3 How to restart deepstream without root

Useful to know, since `systemctl` needs privileges but this does not — it is the same clean path
`main.py` takes on `SIGINT`, and systemd's `Restart=always` brings it back:

```bash
docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)
```


### 14.4 Upload switches and data-loss fix — 2026-10-23

#### What you can switch

`/opt/apps/gcs/control/upload.conf` (editable as `xnx`, no sudo):

```ini
UPLOAD_ENABLED=true        # false: nothing uploaded, nothing deleted; files stay in /media/data/{images,meta,recordings}
DELETE_AFTER_UPLOAD=true   # false: after a successful upload, move files to /media/data/uploaded/<dir>/ instead of deleting
```

- Values: `true/false`, `yes/no`, `on/off`, `1/0`, any case. A missing file means both `true`
  (the original behaviour). An invalid value keeps the default and logs a warning.
- The file is **re-read at the start of every cycle** (every 15 min), so no restart is needed. To
  apply a change immediately, `docker stop gcs`: systemd restarts it and it runs a cycle straight
  away.
- Each cycle logs the active mode to `/var/shared/logs/gcs.txt`:
  `Upload mode: UPLOAD_ENABLED=False DELETE_AFTER_UPLOAD=True`, and with uploads off,
  `Uploads disabled: leaving N file(s) in /media/data/recordings`.
- `DELETE_AFTER_UPLOAD=false` moves files rather than leaving them in place so they are not
  uploaded again every 15 minutes. Nothing ever cleans `/media/data/uploaded/`; delete from it by
  hand.

#### The bug fixed along the way

The shipped `GCS.upload_blob()` caught every exception and returned normally, and the uploader then
ran `os.remove()` unconditionally. **A failed upload deleted the file.** `upload_blob()` now returns
`True`/`False`. On failure the file stays where it is and is retried next cycle, whatever
`DELETE_AFTER_UPLOAD` says.

#### How it is wired

| Path | Purpose |
|---|---|
| `/opt/apps/gcs/app-override/` | the gcs app code, copied from the image, with three changes: `uploader.py` (switches), `cloud/adapters/gcs.py` (return value), `main.py` (one line, logs the mode each cycle) |
| `/opt/apps/gcs/control/` | the switch file; mounted as a **directory** so editors that replace the file are still seen |
| `/opt/apps/gcs/docker-compose.yaml` | two read-only mounts added; original kept as `docker-compose.yaml.orig-20261023` |

#### Verification

- Eight unit tests in a throwaway gcs container with a fake cloud connector, so the real bucket was
  never touched: default behaviour, upload off, keep-local move, upload failure with delete on and
  off, parsing edge cases, a change picked up without restart, and the adapter's return value. All
  pass.
- In production with `UPLOAD_ENABLED=false`: the first cycle logged the mode and
  `leaving 16 file(s) in /media/data/recordings`, and the files stayed.
- **Not yet exercised in production:** the `DELETE_AFTER_UPLOAD=false` move, because that needs a real
  upload. It is covered by the unit tests, and the uploader runs as `uploader:shared`, which can write
  `/media/data`.

**To revert:** restore `docker-compose.yaml.orig-20261023`, then `docker stop gcs`.


### 14.5 LED now means "frames are flowing" — 2026-10-23

`/opt/apps/deepstream-monitoring/launch.sh` (original kept as `launch.sh.orig-20261023`). The LED is
now off only when **all** of these hold:

1. the heartbeat is under 30 s old (unchanged);
2. `docker logs --since 30s --tail 200 deepstream_app` contains a `**PERF` line (nvdslogger prints
   one every 5 s once the pipeline is `PLAYING`);
3. no camera in the latest `PERF` line reports a zero frame rate.

Also, a missing heartbeat file now turns the LED on; previously it left the LED as it was.

**Two traps found while testing, both avoided now. Read this before editing the script:**
- The system `awk` is **mawk**, which compared the field `"0.00"` with `0` as text, so a stalled
  camera passed as healthy.
- Forcing a numeric comparison then broke under the `en_DK` locale (comma decimals): `"0.20"`
  parsed as `0`, so any rate under 1 FPS would have been flagged as stalled. The script now matches
  zero as text (`grep -qxE '0+(\.0+)?'`), which is locale-independent.

**Verification.** 12 stub cases (fake `docker` and `set_led.sh`) pass under the `C`, `en_DK` and
`en_US` locales: healthy, crash loop, one or both cameras at 0, `0` without decimals, slow but alive
(0.20/0.05 and 0.01), `10.00` not mistaken for zero, an older good line followed by a stalled latest
one, stale heartbeat, missing heartbeat, and a missing container. Live, the LED went on during a
deepstream restart (`No frame rate reported in the last 30 s`) and off again 30 s later once frames
resumed.

**Behaviour to expect.** The LED is now yellow for up to about a minute after every deepstream start,
which is accurate: the unit is not capturing yet. After a crash it can take up to 30 s to turn
yellow, because frame-rate reports from just before the crash are still inside the 30 s window.

**Restarting monitoring without sudo:** `deepstream-monitoring.service` has
`Requires=deepstream.service`, so restarting deepstream (§14.3) restarts it too. With sudo:
`sudo systemctl restart deepstream-monitoring`.

**To revert:** copy `launch.sh.orig-20261023` back over `launch.sh` and restart as above.


### 14.6 LED check reads the log tail — 2026-11-16

**Symptom:** the LED was yellow although the pipeline was running at ~1.1 frames/s per camera. The
monitor logged `No frame rate reported in the last 30 s`.

**Cause:** the check ran `docker logs --since 30s`, which scans the container's log file from the
beginning. The deepstream container is the same one since 2026-09-08, never recreated, so its log had
grown to **1.2 GB**, with 6 lines damaged by power cuts (NUL bytes). The scan took 31 s and returned
nothing. Reading from the end (`--tail`) is unaffected and instant.

**Fix:** `frames_flowing()` now reads `docker logs --timestamps --tail 50`, checks the age of the
newest `PERF` line itself (older than 30 s means no frames), and wraps the call in a 10 s timeout.
Verified with 15 stub cases under three locales (45/45), including a report 120 s old, an unreadable
timestamp and a hung `docker logs`. Live: LED on during a deepstream restart (`Last frame rate report
is 38 s old`), off once frames resumed; each check takes about 0.1 s. Previous version kept as
`launch.sh.prev-20261116`.

**Recommended follow-up:** bound the container logs by adding to each compose service
`logging: {driver: json-file, options: {max-size: 10m, max-file: "3"}}`. This recreates the containers
and discards their old logs. Their content is duplicated in the journal and syslog, and was archived
on 2026-10-23.


### 14.7 Office network preferred, and a local mirror of all cloud data — 2026-11-16

**Network.** A second cable on `eth2` gives office internet (`10.122.85.0/24`). Both `eth1` (camera
switch + 4G router) and `eth2` offered a default route, and the 4G one won (metric 100 vs 101). The
`eth2` profile ("Wired connection 3") now has `ipv4.route-metric 50` and `ipv6.route-metric 50`, so
office internet is preferred and 4G stays as a fallback. The camera network is unaffected. Measured
~42 MiB/s via `eth2` against ~4 MiB/s via 4G.

**All project buckets, sized 2026-11-16:**

| Bucket | Size | Content |
|---|---|---|
| `data-biodiversity` | 232.4 GB | all units' images, metadata, recordings; two dataset zips (§7) |
| `artifacts-bio` | 212.7 GB | `swedish-recordings/` 207 GB of raw 1080p/4K field video (Oct 2024); `jetson-os/` 2.9 GB OS image; `datasets/`; `apps/` deployment packages; a Darwin annotation export |
| `data-roadkill` | 12.7 GB | `annotations/`, `images/`, `artifacts/`: a labelled roadkill dataset |
| `models-bio` | 1.2 GB | model weight history |
| `vd-website` | 0.5 GB | |
| `data-bio` | 0.1 GB | 380 older recordings |

**Mirror job.** Everything (~460 GB) is being copied to `/media/data/gcs-archive/<bucket>/` on the
Samsung T7 SSD (865 GB free before the copy) by a user service that survives reboots and power cuts:

| | |
|---|---|
| job | `~/gcs-archive-job/archive.sh`, bucket order in `buckets.txt` (delete a line to skip a bucket) |
| service | `systemctl --user status gcs-archive` (user `xnx`, lingering enabled so it runs without a login) |
| progress | `~/gcs-archive-job/status.sh` |
| logs | `/media/data/gcs-archive/logs/<bucket>.log` |
| per bucket | `<bucket>.manifest.csv` (name, size, crc32c, md5 of every object) and `<bucket>.complete` once verified |

For each bucket the job writes the manifest, runs `gcloud storage rsync` (which checks each file's
hash as it downloads, and resumes where it stopped), then verifies every object against the manifest.
A bucket is marked complete only when verification passes; on any failure systemd retries after 2 min.

**Do not let the access key be rotated until every bucket shows `complete`.** Rotating it is the one
thing that would cut this access. Rewriting the repository history (Issue 9b) does not affect it.


**Result (2026-11-16, 14:15–17:49): complete and verified.** All six buckets plus the cloud-function
source bucket are on the SSD, about 460 GB. Each one matches its manifest exactly: every object
present at the right size, and gcloud checks each file's hash while downloading.

| Bucket | Objects | GB |
|---|---|---|
| `data-biodiversity` | 288,699 | 232.39 |
| `artifacts-bio` | 6,992 | 212.66 |
| `data-roadkill` | 2,124 | 12.70 |
| `models-bio` | 15 | 1.23 |
| `vd-website` | 136 | 0.46 |
| `data-bio` | 379 | 0.10 |
| `gcf-v2-sources-…` | 2 (+2 older versions) | 0.02 |

Notes from the run:
- **Faster than estimated:** about 3.5 h in total. gcloud downloads large files in parallel slices.
- **Versioned bucket:** only `gcf-v2-sources-…` (the deployed cloud-function code) keeps old object
  versions. rsync fetches only the current one, so the older generations were fetched by generation
  number and saved as `function-source.<date>.gen-<n>.zip`. `verify.py` now fails if a manifest
  repeats a name, so this can't pass silently again.
- **Not retrievable with this key:** the Firestore search database (no permission). It is derived
  from the `meta/*.json` files, which are now local.
- **Unit behaviour under the load:** no reset (load average above 30; input rail never below 4.936 V,
  peak 3.2 A). That argues against an overloaded supply in Issue 10. The rear camera's stream dropped
  twice (15:27, 16:15; `Internal data stream error`) and deepstream recovered on its own within about
  a minute each time. Most likely CPU starvation of the GigE receive path during the download.

The mirror is a single copy, on the same unit that suffers power cuts. Copy it offsite.
