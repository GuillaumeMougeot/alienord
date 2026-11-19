# GPU power issue on the roadside unit: what was wrong and how it was fixed

**Date:** 19 November 2026 · **Unit:** bluemar-bio-xnx-2 (Lenovo SE70 with an NVIDIA Jetson Xavier NX)
· Plain-language summary for reporting. Details: [journal](../journal/2026-11-19-can-the-gpu-driver-be-fixed.md),
[runbook](../docs/gpu-driver-fix.md).

## In one sentence

A bug in NVIDIA's graphics driver made the unit's graphics chip run at full speed and use about
8 W more than it should. We rebuilt the driver with NVIDIA's own later fix, and the chip now stays
at its proper limit.

## The problem

- The unit's power supply cuts out when the unit draws about 19 W for a while. Normally it draws 11–12 W.
- On 17 and 18 November the unit lost power some time after someone had played a video or opened
  Firefox on it.
- The cause: playing a video or starting Firefox made the graphics chip (GPU) jump from its set
  limit of 510 MHz to its maximum of 1109 MHz, and stay there until the next restart. That added
  about 8 W, which put the unit at about 19.4 W, right at the supply's limit.
- The video player and Firefox were not to blame. It is a bug in NVIDIA's driver in the system
  version installed on this unit (L4T 35.1). NVIDIA fixed it in the next version (L4T 35.2.1).

## What we did

1. **Stopgap (18 November):** a small watchdog service that notices the stuck speed and pulls it
   back down within about 10 seconds. It stays installed as a backup.
2. **Real fix (19 November):** we took NVIDIA's public source code for the driver on this unit,
   added only NVIDIA's own correction from the next version, and built it for this unit's exact
   system. Before adding the fix, we checked that our build without it matched the original
   driver exactly.
3. **Testing:** we first ran the new driver for a single start-up, set up to go back to the
   original driver on its own if anything went wrong. Once it passed, we made it permanent.

## Result

- Playing a video and starting Firefox no longer push the graphics chip above 510 MHz. During 30
  seconds of measurement around opening a 4K video, the speed never left 510 MHz, and the backup
  watchdog never had to step in.
- Recording runs normally (about 1.4 frames per second per camera, as before).
- The original driver was not changed or deleted. It stays on the disk next to the new one.

## Safety net

- If the new driver ever crashes the unit, the unit restarts by itself and from then on uses the
  original driver, until someone looks into it. Power cuts are not counted as crashes.
- Going back to the original by hand is one command, and removing the fix completely means
  deleting one file. Step-by-step instructions: [docs/gpu-driver-fix.md](../docs/gpu-driver-fix.md).
- The same fix can be installed on an identical unit with one command, after an automatic check
  that the unit really is identical.

## Lessons along the way

- Swapping the driver while the unit is running crashes it, even with the original driver. Our
  first two tests did exactly that. Nothing was lost and the unit restarted on its own, but driver
  changes must only take effect at a restart.
- The unit has a hardware watchdog: after a freeze, it restarts the unit by itself within a few minutes.

## Still to check

- The first restart with the new driver froze at its very last step, and the watchdog finished it
  (about 3 minutes). Nothing was lost and the unit came back normally. One more restart will show
  whether this happens every time; if so, restarts simply take a few minutes longer.

## Longer term

- Moving the unit to a newer NVIDIA system version (L4T 35.2.1 or later) would include this fix
  officially, but that means a full reinstall from Lenovo's images.
