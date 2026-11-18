# Why are the recorded images so dark?

**Kind:** investigation · **Status:** RESOLVED (2026-09-08): the cameras are set for driving in
daylight. The side camera's longest exposure is 200 µs, which is near-black indoors. Not changed.

The camera settings in `configs/config.yaml` are applied with `arv-tool` at every app start:
`AutoExposureTimeMax` 200 µs on the side camera and 1000 µs on the rear, with auto gain capped at
24 dB. That freezes motion at 100 km/h but collects almost no light indoors, and gain cannot make up
a 200-fold shortfall. Trifork's own troubleshooting note suggests 40000 µs for bench tests. Settings
changed with `arv-tool` are reverted at the next app start, so a lasting change must go through a
config override. How: [`../docs/configuration.md`](../docs/configuration.md#camera-exposure).
Revert before driving: 40 ms at 80 km/h is about a metre of blur.
