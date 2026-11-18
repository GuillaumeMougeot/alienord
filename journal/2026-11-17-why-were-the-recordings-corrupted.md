# Why were the 23 October recordings corrupted?

**Kind:** investigation · **Status:** RESOLVED (2026-11-17): each was cut off by the power loss that
followed its button press. Linux keeps written file contents in memory for up to 30 s before saving
them to disk, so the frames existed as files but their contents were never saved. The recording code
is not at fault.

## Evidence

- `vm.dirty_expire_centisecs = 3000`: written data waits up to 30 s before going to disk. The SSD is
  ext4 in `ordered` mode, which records new files in its journal every 5 s.
- The 16:18:56 recording: frames written 16:18:56-16:19:01. The first four have content but are cut
  short (no JPEG end marker); the last twelve are **0 bytes**: recorded as existing, never filled in.
  The power went within seconds of 16:19:01.
- After each reset the kernel logged `EXT4-fs (sda1): recovery complete` and `orphan inodes deleted`:
  an unclean shutdown.
- All three 2026-10-23 recordings show this (6/7, 15/16 and 12/16 frames empty). The eight
  recordings of 2026-09-08 are intact: nothing cut the power within 30 s of them.

## Where every recording is

| When (local) | Where | Frames | State |
|---|---|---|---|
| 09-08, 7 presses + 1 software test | `/media/data/gcs-archive/data-biodiversity/recordings/bluemar-bio-xnx-2/` | 59 | valid, with GPS |
| 10-23 13:27:57 | same | 7 | 6 empty, 1 truncated |
| 10-23 14:19:16 | `/media/data/recordings/` | 16 | 15 empty, 1 truncated |
| 10-23 16:18:56 | `/media/data/recordings/` | 16 | 12 empty, 4 truncated |

## Next try

Start the recording in software, not with the button, then wait 30 s (or run `sync`) before anything
could cut the power: [`../docs/operations.md`](../docs/operations.md#recording-with-the-button). It
doubles as test 1 of [the reset question](2026-10-23-why-does-the-unit-reset.md). For usable indoor
frames, raise the exposure first ([configuration](../docs/configuration.md#camera-exposure)), or put
the camera at a window. Optional, with sudo: `sysctl vm.dirty_expire_centisecs=500` would shrink the
loss window from 30 s to 5 s, at a small cost in disk writes.
