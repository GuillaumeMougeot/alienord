# Why was the LED green during a six-week outage?

**Kind:** change · **Status:** RESOLVED (2026-10-23): the heartbeat meant "the app started", not
"frames are flowing", and fast restarts kept it fresh. The LED now also requires a recent, non-zero
frame rate. A mistake of ours: the engine-cache fix of 2026-09-08 caused the blind spot.

## Cause

The app writes its heartbeat once when it reaches `Running...`, even if it dies 10 ms later. With
13-minute restarts the heartbeat went stale and the LED was yellow. After the
[engine-cache fix](2026-09-07-why-does-every-restart-take-13-minutes.md) a crash-and-restart took
~30 s. Across the outage the gap between heartbeats was median 31 s, p90 38 s, against a 30 s limit,
so the LED was yellow **8.1 % of the time**. For six weeks the unit captured nothing and the lamp
mostly said it was fine.

## Change

`/opt/apps/deepstream-monitoring/launch.sh` (original kept as `launch.sh.orig-20261023`): the LED is
off only if the heartbeat is fresh **and** the latest `PERF` line (nvdslogger, every 5 s) shows a
non-zero rate for every camera. A missing heartbeat file now lights it too.

## Two traps found by testing

- The system `awk` is **mawk**: it compared `"0.00"` with `0` as text, so a stalled camera passed.
- Forcing a number then broke under the `en_DK` locale: `"0.20"` parsed as 0, so anything under
  1 fps raised a false alarm. The check now matches zero as text, independent of locale.

12 stub cases pass under the C, en_DK and en_US locales. Live, the LED went on during a restart and off
once frames resumed. A later flaw (a slow log query) was fixed on 2026-11-16:
[why the LED was yellow while frames flowed](2026-11-16-why-is-the-led-yellow-when-frames-flow.md).
