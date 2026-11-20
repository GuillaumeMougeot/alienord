# Can a second unit (xnx1) get bluemar-bio-xnx-2's fixes, now that its GPU driver is fixed?

**Kind:** change · **Status:** RESOLVED (2026-11-20): yes. On xnx1, uploads are off, the AI engines
are cached (restart 10.5 min → 22 s) and the LED checks frame flow, all applied by
[`tools/stock-unit-fixes.sh`](../tools/stock-unit-fixes.sh) (owner, sudo, 2026-11-19 16:47-17:10).
`tools/unit-mode.sh` says READY. Two of the script's own checks were wrong; both are fixed.

Times are local (CET) unless marked UTC.

## The question

A clone of this repository was opened on a second unit, `xnx1`, where the GPU driver fix had just been
installed (`tools/nvgpu-fix/perm/install-nvgpu-fix.sh`). The owner asked for the commands to (1) fix
the LED being yellow, (2) check that everything works, and (3) stop uploads to Trifork's bucket.

## What xnx1 is

**A stock Trifork unit.** Apart from the GPU fix (fixed driver loaded, `taint` = `O`, GPU at
510/510 MHz), it has none of bluemar-bio-xnx-2's changes. It is not just a second copy:

| | bluemar-bio-xnx-2 | xnx1 |
|---|---|---|
| deepstream image | `fcded2a42c5e` | `28fc81013fc6`: **no plant model**, only `car` and `roadkill` |
| gcs image | `aa294dcf3b92` | `aa294dcf3b92`, the same: the patched uploader applies as is |
| `/media/data` | separate 931 GB SSD | a folder on the system NVMe: **its 931 GB SSD is plugged in but not mounted there** ([11-20](2026-11-20-why-are-xnx1s-recordings-not-on-the-ssd.md); first written here as "no separate SSD", which was wrong) |
| system journal | persistent | in memory only: on 11-20 it started at 06:36 though the unit had been up since 11-19 16:22 |
| Trifork's `monitoring` container | absent | running |
| LED script `launch.sh` (original) | heartbeat only | heartbeat only, and reports old files to Trifork's JFrog fleet API with the tokens in `/var/secrets/jfrog_*` |
| `xnx` in group `apps` | yes | **no**: every change in `/opt/apps` needs sudo |
| `~/vd-biodiversity`, `/var/secrets/bot.env` | present | absent: the commit hook cannot run (below) |

**What was wrong at 16:37 on 11-19:**

- **LED yellow for 11 min after every start** (16:22:56 to 16:33:57 on that boot), then off. This
  was the [13-minute restart](2026-09-07-why-does-every-restart-take-13-minutes.md) again: the app
  cannot save its compiled models (folder owned by uid 1000, app runs as uid 116), so it rebuilds them
  at every start and writes no heartbeat meanwhile. Not a fault in the LED script.
- **Uploads on.** Every 15 min to Trifork's bucket, with Trifork's uploader, which
  [deletes files even when the upload fails](2026-10-23-upload-switches-and-the-delete-on-failure-bug.md).
  `/media/data/images`, `meta` and `recordings` were empty.
- The LED script was blind to a crash loop
  ([10-23](2026-10-23-why-was-the-led-green-during-the-outage.md)).

`tools/unit-mode.sh status` already said READY then (production exposure, both cameras ~2 and 3 fps),
plus "uploads on". Its "data disk" line was in fact the system disk; it now requires a mounted disk.

## The change

Three steps, copied from bluemar-bio-xnx-2 (`device/bluemar-bio-xnx-2/`), in one script run with
sudo. Every replaced file is kept as `*.orig-20261119`; the script's output is in
`/var/log/alienord-stock-unit-fixes.log` on xnx1.

1. **Uploads off:** `/opt/apps/gcs/app-override/` (patched uploader), `/opt/apps/gcs/control/upload.conf`
   (`UPLOAD_ENABLED=false`) and bluemar-bio-xnx-2's `docker-compose.yaml` (mounts both, logs capped at
   3 × 10 MB). Only if the gcs image is `aa294dcf3b92`; otherwise the script stops `gcs.service`.
2. **Model cache:** the container copied its own models to `/media/data/models` (9 files,
   109,744,132 bytes, as `app:shared`), and one line in `/opt/apps/deepstream/docker-compose.yaml`
   mounts it over the image's folder.
3. **LED:** bluemar-bio-xnx-2's `launch.sh` (heartbeat **and** a recent, non-zero frame rate per
   camera). This also drops the original's report to Trifork's JFrog fleet API.

## Verification

From the script's log and the app's own log (`/var/shared/logs/deepstream.txt`, UTC):

| | |
|---|---|
| uploads | gcs log at every cycle since: `Upload mode: UPLOAD_ENABLED=False DELETE_AFTER_UPLOAD=True` (last checked 11-20 07:32 UTC) |
| restart 1 (builds engines) | signal 15:48:10 UTC → `Running...` 15:58:39 UTC: **10.5 min**. Engines saved: car 1,959,003 B, roadkill 154,757,954 B |
| restart 2 (loads them) | signal 15:58:59 UTC → new container 15:59:06 → `Running...` 15:59:21 UTC: **22 s**. No `failed to serialize` |
| LED | 17:09:38: `Frame rate: FPS_0 (2.00) FPS_1 (3.50)`, `Heartbeat ok`, `LED: off`; not on once in what the journal still holds (11-20 06:52 to 08:46; earlier entries rotated away) |
| readiness | 11-20 08:43: READY FOR PRODUCTION, one warning (uploads off); GPS has a fix this morning |

## Our mistakes

- **I first gave the steps as a list of commands, and on 11-19 the owner reported they had been run.
  They had not reached xnx1.** No file had changed, the containers were the boot ones, and the
  system log showed only one sudo since boot (`apt install tmux`). Checking before writing
  this journal caught it. Likely cause: a sudo password prompt. Hence one script, run once with
  `sudo`, that logs to a file.
- **The script's own checks reported two failures where there were none:**
  - *Uploads:* it waited for `Uploads disabled`, which the uploader only logs when files are waiting.
    xnx1 had none. Now it reads the `Upload mode:` line logged at every cycle.
  - *Restart 2:* it waited 600 s for a frame-rate (`PERF`) line in `docker logs --tail 20` and gave up,
    though the app was running after 22 s. A `PERF` line sits in the last 20 lines about half the
    time, so 120 polls should have found one. Run as `xnx`, the same loop finds it at once. **The
    cause is not found**; root under sudo is the only difference left, and that could not be tested
    without the password. The script now waits for a new container and a `Running...` line in the
    app log written after the signal, the check CLAUDE.md already prescribes. Tested on the
    11-19 log: it finds restart 2 and rejects an older line. `tools/unit-mode.sh`'s `restart_app`
    uses the same `docker logs | grep -q PERF` pattern and has worked on bluemar-bio-xnx-2; left as is.
- **In my first reading on 11-20 I said the unit had restarted overnight** because the journal began
  at 06:36. It had not (`uptime -s`: 11-19 16:22:37); xnx1's journal is in memory and rotates.

## Not committed from xnx1

`tools/check-secrets.sh` needs five live values, read from `/var/secrets/bot.env` and the private
repository `~/vd-biodiversity`; neither exists on xnx1, so the hook aborts every commit, and it is not
to be bypassed. It also does not know xnx1's JFrog tokens. These files were checked by hand on xnx1
against the gcs key ID and both JFrog token values, and the hook's patterns: clean. To be committed
from bluemar-bio-xnx-2, or after deciding how the hook should behave on a unit without those files.

## Left open

- xnx1's other stock settings: no persistent journal, no log rotation, uncapped logs for gps and
  deepstream, `updates.service` and Trifork's `monitoring` container running. Not touched.
- Whether xnx1's missing plant model is intended (it is the side-camera model on bluemar-bio-xnx-2).
