# Findings

Section 1 is what has been established about the system, one line each; section 2 is every change
made to the unit. The reasoning is in the linked [`journal/`](journal/README.md) entries.

## 1. What is established

| # | finding | journal |
|---|---|---|
| 1 | **The unit's resets are input-voltage collapses**: the power chip records undervoltage at every one (`0x54`/`0x44`), and `0x0` at clean reboots. Not software or heat; probably not an overloaded supply (3.5 h at load average 30, no sag). | [10-23](journal/2026-10-23-why-does-the-unit-reset.md) |
| 2 | **The supply cuts out under sustained high load**: at ~19.4 W (normal ~11-12 W) it held 40 min (11-17) and 70 min (11-18), then cut out, with the 5 V rail steady until the cut: its protection tripping once warm, at its rated limit (~19 W, owner). Both loads were a stuck GPU clock (#16), not the apps. Short and long presses at normal load do not reset. (Earlier "button wiring" conclusion withdrawn.) | [10-23, update 11-17](journal/2026-10-23-why-does-the-unit-reset.md#update-2026-11-17-a-reset-with-no-press-caught-by-the-power-logger) |
| 3 | Data written in the last ~30 s before a power cut is lost (Linux write-back delay); this destroyed all three 10-23 recordings. | [11-17](journal/2026-11-17-why-were-the-recordings-corrupted.md) |
| 4 | One power feed supplies the cameras, switch and 4G router: one knock removes vision and remote access together. | [09-08](journal/2026-09-08-why-did-the-camera-stream-drop.md) |
| 5 | The unit captured nothing from 2026-09-08 to 10-20: the camera side was down and the app crashed 118,431 times. Cause unknown. | [10-23](journal/2026-10-23-was-anything-captured-since-september.md) |
| 6 | A heartbeat proves only that the app started; fast restarts kept it fresh during the outage (LED yellow 8.1 % of the time). The LED now checks frame flow. | [10-23](journal/2026-10-23-why-was-the-led-green-during-the-outage.md) |
| 7 | The shipped uploader deleted files even when the upload failed. Fixed. | [10-23](journal/2026-10-23-upload-switches-and-the-delete-on-failure-bug.md) |
| 8 | All project data is ~460 GB in seven buckets of Trifork's Google Cloud project, private, in Belgium. It holds all five units' data and 207 GB of Swedish field video. Copied and verified locally. | [11-16](journal/2026-11-16-retrieving-all-cloud-data.md) |
| 9 | The unit's cloud key is live and also in Trifork's Git history (since 2023); Trifork's GitHub token is revoked. | [11-16](journal/2026-11-16-credentials-in-trifork-history.md) |
| 10 | Nothing is rebuildable without Trifork's private `core` framework; it was recovered intact. | [09-08](journal/2026-09-08-what-would-we-lose-without-trifork.md) |
| 11 | `nvinfer` writes engines next to the model file and ignores `model-engine-file` for writing. | [09-07](journal/2026-09-07-why-does-every-restart-take-13-minutes.md) |
| 12 | The cameras are set for daylight driving (exposure ≤ 200 µs): 1.2/255 indoors. 40 ms: 30/255; 100 ms: 66.8/255. | [09-08](journal/2026-09-08-why-are-the-images-dark.md), [11-17](journal/2026-11-17-can-the-cameras-see-indoors.md) |
| 13 | The GPS receiver works but sees no satellites indoors. | [10-23](journal/2026-10-23-why-does-the-gps-have-no-fix.md) |
| 14 | The running code differs from the repository's `main`; the log claims cameras are configured when they are absent; 6 more defects. | [09-08](journal/2026-09-08-what-is-wrong-in-the-code.md) |
| 15 | On this unit, `awk` is mawk and the locale uses comma decimals: text-vs-number and `printf` traps, met three times. | [10-23](journal/2026-10-23-why-was-the-led-green-during-the-outage.md) |
| 16 | **Hardware video decoding and Firefox's start-up leave the GPU clock at 1109 MHz**, above the power mode's 510 MHz cap, until reboot (+8 W). Cause: the L4T 35.1 GPU driver's clock arbiter falls back to the maximum and ignores the cap (NVIDIA fixed it in 35.2.1). Lowering the cap one step and restoring it resets the clock; `gpu-clock-guard` does this within ~10 s. With it, hardware-decoded 4K playback costs ~1 W. | [11-18](journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md) |

## 2. Changes made to the unit

Each keeps the original beside it. **How to undo each one: [`docs/reverting.md`](docs/reverting.md).** Mirror: [`device/`](device/README.md).

| date | change | where | journal |
|---|---|---|---|
| 09-08 | recovery backup (framework, images, models, code, config) | `/media/data/backup/`, `~/backup/` | [09-08](journal/2026-09-08-what-would-we-lose-without-trifork.md) |
| 09-08 | models on the SSD, mounted into the container: restarts 13 min → 26 s | `/opt/apps/deepstream/docker-compose.yaml`, `/media/data/models/` | [09-07](journal/2026-09-07-why-does-every-restart-take-13-minutes.md) |
| 10-23 | upload switches; failed uploads keep files; **uploads off** | `/opt/apps/gcs/` | [10-23](journal/2026-10-23-upload-switches-and-the-delete-on-failure-bug.md) |
| 10-23 | LED requires frame flow | `/opt/apps/deepstream-monitoring/launch.sh` | [10-23](journal/2026-10-23-why-was-the-led-green-during-the-outage.md) |
| 10-23 | logrotate installed + app-log rule; journal persistent (owner, sudo) | `/etc/logrotate.d/`, `/var/log/journal/` | [10-23](journal/2026-10-23-logs-grow-without-bound.md) |
| 11-16 | LED check reads the log tail | `/opt/apps/deepstream-monitoring/launch.sh` (`.prev-20261116`) | [11-16](journal/2026-11-16-why-is-the-led-yellow-when-frames-flow.md) |
| 11-16 | input-power logger (owner, sudo) | `/opt/apps/power-log/`, `vd-power-log.service` | [10-23](journal/2026-10-23-why-does-the-unit-reset.md) |
| 11-16 | office network preferred over 4G | NetworkManager "Wired connection 3", metric 50 (was default) | [11-16](journal/2026-11-16-retrieving-all-cloud-data.md) |
| 11-16 | cloud mirror job; lingering enabled for `xnx` | `~/gcs-archive-job/`, `/media/data/gcs-archive/` | [11-16](journal/2026-11-16-retrieving-all-cloud-data.md) |
| 11-17 | **indoor exposure**: 100 ms cap on both cameras. **Revert before driving** | `/opt/apps/deepstream/config-override/config.yaml`, compose mount | [11-17](journal/2026-11-17-can-the-cameras-see-indoors.md) |
| 11-18 | **GPU clock guard** (owner, sudo) | `/opt/apps/gpu-clock-guard/`, `gpu-clock-guard.service` | [11-18](journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md) |
| 11-18 | container logs capped at 3 × 10 MB each | the three `docker-compose.yaml` | [11-18](journal/2026-11-18-capping-the-container-logs.md) |
