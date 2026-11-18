# Why does the unit not record, with the yellow LED on?

**Kind:** incident · **Status:** RESOLVED (2026-09-08): the camera network cable had been moved to a
guest network, so the app crash-looped; each restart then spent 13 minutes rebuilding its AI engines.

## What was observed

The unit started but never recorded, and the yellow LED was on. The LED turned out to mean only
"the app's heartbeat is more than 30 s old" (`deepstream-monitoring/launch.sh`), not a specific fault.

## What was found

- The app reached `Running...` and died within milliseconds: `Could not find camera
  "…FAA22080468"`. It had done this 132 times in its log.
- NetworkManager showed `eth1` losing carrier at 15:50:57 on 09-07 and coming back on a different
  network: `10.122.85.50`, domain `guest.local`. The cameras live on `192.168.2.x`, so discovery found
  nothing. `arv-tool-0.8` confirmed it: `No device found`.
- Each restart rebuilt three TensorRT engines from scratch (~13 min), so the app was alive for under a
  second every 13 minutes and the LED was yellow throughout. See
  [why every restart takes 13 minutes](2026-09-07-why-does-every-restart-take-13-minutes.md).
- The log was misleading: every start printed `Successfully configured camera …` even with no
  cameras. See [what is wrong in the code](2026-09-08-what-is-wrong-in-the-code.md).

## Resolution

The owner moved the guest cable to `eth2` and the camera cable back to `eth1` (2026-09-08 13:30). The
next build finished at 13:36 and the unit recorded: 3 button presses gave 21 frames, uploaded at
13:43. They seemed to vanish because the uploader deletes local copies after upload; see
[where the images go](2026-09-08-where-do-the-images-go.md).
