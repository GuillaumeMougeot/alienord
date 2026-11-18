# Can the cameras take usable pictures indoors?

**Kind:** change · **Status:** RESOLVED (2026-11-17): yes, with the exposure cap raised to 100 ms.
Brightness went from 1.2/255 (0.2 ms) to 30/255 (40 ms) to **66.8/255 (100 ms)**, with the camera
under a table. **Revert before driving:**
[`../docs/reverting.md`](../docs/reverting.md#indoor-camera-exposure-2026-11-17).

The owner's short button press at 09:10 recorded 3 complete frames with a mean brightness of
**1.2/255**: black, as expected from [the dark-images entry](2026-09-08-why-are-the-images-dark.md).

**Change:** a copy of the image's `configs/config.yaml` in `/opt/apps/deepstream/config-override/`,
with `AutoExposureTimeMax` set to 40000 µs on both cameras (rear was 1000, side 200), mounted over
the original. The image's version is kept as `config.yaml.pristine`; the compose file as
`docker-compose.yaml.before-exposure-20261117`. Changing the compose file recreates the container,
which also discarded the old container's 1.2 GB log; its history survives in the app logs and
`~/backup/logs-20261023/`.

**Result:** a software-started recording gave 7 frames, mean **30.2/255**, ~330 KB each (against
~158 KB when black). Auto-exposure now sits at the 40 ms cap, and gain is already at its 24 dB
maximum, so to go brighter raise the cap further (100 ms ≈ 2.5× brighter; the side camera's 5 fps
allows up to 200 ms) or add light.

**A mistake on the way:** my first readiness check matched a frame-rate line from the *old*
container, so the config check and test recording ran against a container that was shutting down.
Wait for a new `Running...` in `/var/shared/logs/deepstream.txt` and a new container ID.

**Open:** why this morning's press gave 3 frames instead of the usual 7. Written 1.2 s apart, then
none in the last 2 s of the window. The 10:05 recording gave 7.

**Same-day follow-up, at the owner's request:** cap raised to 100 ms (100000 µs) on both cameras.
The file was rewritten in place, because the container bind-mounts that single file; a plain
deepstream restart applied it (the compose file was unchanged). A software-started recording gave 6
frames at **66.8/255**, about 2.2× the 40 ms result, as expected. Module current normal (2.9 A).
