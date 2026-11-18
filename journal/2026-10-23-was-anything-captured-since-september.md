# Was anything captured between September and October?

**Kind:** incident · **Status:** RESOLVED (2026-10-23): no. From 2026-09-08 17:28 to 2026-10-20 the
app crash-looped 118,431 times, because the cameras were gone. Why they were gone cannot be
established.

## Evidence

- The last good run (98 min) ended on 2026-09-08 at 17:28 local with `Internal data stream error
  (-5)`, the same signature as a camera power or link loss. After that, every start failed with
  `Could not find camera …468`, ~2,500-3,700 times a day, until the unit was switched off on 2026-10-20.
- The GPS kept working throughout, so the Jetson was up and only the camera side (cameras, switch, 4G
  router: one power feed) was down. Powering everything on again on 2026-10-23 brought the cameras
  straight back.
- No recordings, no detections and no uploads in those six weeks.
- **Why** the camera side stayed down is unknown: the journal was volatile, so the network history
  was lost at the next boot. It is persistent since 2026-10-23
  ([logs](2026-10-23-logs-grow-without-bound.md)).

## Why nobody noticed

The LED stayed mostly off. See [why the LED was green during the outage](2026-10-23-why-was-the-led-green-during-the-outage.md).
