# Why did the camera stream drop an hour after the fix?

**Kind:** incident · **Status:** RESOLVED (2026-09-08): the owner had bumped the power cable shared by
the cameras, switch and 4G router.

At 14:02:46 the kernel logged `igb eth1: NIC Link is Down`, back up two seconds later. At 14:03:05 the
app died with `Internal data stream error (-5)`, and the retry at 14:16:56 failed again: both cameras
errored 57 ms after starting, because they had not yet released their streams. The owner confirmed
the bump. The real finding is the design: **one feed powers the cameras, the switch and the 4G
router**, so one knock removes all vision and all remote access at once. Recommended: strain relief,
and a separate feed for the router.

A similar stream error ended the last good run before the six-week outage; see
[was anything captured since September](2026-10-23-was-anything-captured-since-september.md).
