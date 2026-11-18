# What is wrong in the code? (review)

**Kind:** investigation · **Status:** RESOLVED (2026-09-08) as a review; none of these is fixed yet.
They are listed in [`../PLAN.md`](../PLAN.md).

| # | Defect | Effect |
|---|---|---|
| 1 | `bio/app/setup_cameras.py` checks for `not_found`, but `arv-tool` prints `not found` and exits 0 | every start logs `Successfully configured camera`, even with no cameras: verified with both disconnected |
| 2 | `bio/app/main.py`: `all_ok, msg = setup_camera(cam)` overwrites instead of accumulating | only the last camera can stop startup, and the error names the wrong one |
| 3 | `core`'s muxer passes `batched-push-timeout = 1/FRAME_RATE` (0.05, an integer in µs, so 0) | the intended `BATCHED_PUSH_TIMEOUT_USEC: 4000000` is never read; may limit throughput |
| 4 | `pgie_plant.txt` has `batch-size=1`; the pipeline sends batches of 2 | slower plant inference |
| 5 | the running code differs from the repository (the roadkill model is on in the image, off in `main`) | read the container, or [`../deployed/`](../deployed/README.md), not the repo |
| 6 | `StatisticsProbe` ignores `statistics.ENABLED`; `Longitude.from_dict` returns a `Latitude`; `button-push.sh` uses `docker ps -a`; the monitor's data-age check mixes ms and s | minor |
| 7 | `/var/secrets/bot.env` and the GCP key are world-readable (`644`); the GitHub token is also in the remote URL in `/opt/code/vd-biodiversity/.git/config` | any account on the unit can read them |
| 8 | after a camera power or link loss, the immediate retry fails (the camera has not released its stream) and there is no backoff | an extra crash per incident |
