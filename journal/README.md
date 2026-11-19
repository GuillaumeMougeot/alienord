# journal/: one entry per question

Each entry asks one question and records the answer, including dead ends and our own mistakes. Files
are named `YYYY-MM-DD-question.md` by the day the question was **opened**, so `ls` shows the order
things were asked. Each declares a **Kind** (`investigation`: understanding behaviour; `incident`:
something broke; `change`: something altered on the unit) and a **Status**. An entry is frozen once
`RESOLVED`; later findings go in a new entry that links back.

You do not read the journal front to back: start from [`../FINDINGS.md`](../FINDINGS.md) or
[`../PLAN.md`](../PLAN.md) and follow a link.

| opened | question | kind | answer |
|---|---|---|---|
| [09-07](2026-09-07-why-does-the-unit-not-record.md) | Why does the unit not record, with the yellow LED on? | incident | Camera cable on the guest network; crash loop |
| [09-07](2026-09-07-why-does-every-restart-take-13-minutes.md) | Why does every restart take 13 minutes? | change | Engines not cacheable; models on the SSD: 26 s |
| [09-08](2026-09-08-what-would-we-lose-without-trifork.md) | What would we lose without Trifork? | investigation | Framework, images, code, data: all secured |
| [09-08](2026-09-08-why-are-the-images-dark.md) | Why are the images so dark? | investigation | Exposure 200 µs, set for driving |
| [09-08](2026-09-08-where-do-the-images-go.md) | Where do the images go? | investigation | Trifork's bucket, deleted locally |
| [09-08](2026-09-08-what-is-wrong-in-the-code.md) | What is wrong in the code? | investigation | 8 defects, none fixed yet |
| [09-08](2026-09-08-why-did-the-camera-stream-drop.md) | Why did the camera stream drop? | incident | Bumped shared power cable |
| [10-23](2026-10-23-was-anything-captured-since-september.md) | Was anything captured since September? | incident | No: 118,431 crashes in six weeks |
| [10-23](2026-10-23-why-was-the-led-green-during-the-outage.md) | Why was the LED green during the outage? | change | Heartbeat ≠ frames; LED now checks frames |
| [10-23](2026-10-23-upload-switches-and-the-delete-on-failure-bug.md) | Can uploads and deletion be switched off? | change | Yes; failed uploads no longer delete |
| [10-23](2026-10-23-why-does-the-gps-have-no-fix.md) | Why does the GPS have no fix? | investigation | Zero satellites in view indoors |
| [10-23](2026-10-23-why-does-the-unit-reset.md) | **Why does the unit reset?** | incident | **OPEN (watching)**: supply cut out at ~19 W, caused by a stuck GPU clock; guarded since 11-18 |
| [10-23](2026-10-23-logs-grow-without-bound.md) | Why do logs grow, and history vanish? | change | Rotation + persistent journal |
| [11-16](2026-11-16-why-is-the-led-yellow-when-frames-flow.md) | Why is the LED yellow while frames flow? | incident | Slow log query; reads the tail now |
| [11-16](2026-11-16-credentials-in-trifork-history.md) | Can this history be published? | incident | No: fresh public history instead; old one kept private |
| [11-16](2026-11-16-retrieving-all-cloud-data.md) | Can all cloud data be copied locally? | change | Yes: ~460 GB, verified |
| [11-16](2026-11-16-one-home-for-everything.md) | Where should the knowledge live? | change | This repository |
| [11-17](2026-11-17-why-were-the-recordings-corrupted.md) | Why were the recordings corrupted? | investigation | Power cut within 30 s of writing |
| [11-17](2026-11-17-can-the-cameras-see-indoors.md) | Can the cameras take usable pictures indoors? | change | 100 ms exposure: 1.2 → 66.8/255 |
| [11-18](2026-11-18-capping-the-container-logs.md) | Can the containers' logs be capped? | change | Yes: 3 × 10 MB each |
| [11-18](2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md) | Why does the power stay high after the video player is closed? | incident | GPU clock stuck at max; guard resets it in ~10 s |
| [11-18](2026-11-18-publishing-the-repository.md) | Can the knowledge base go public? | change | Yes: alienord, fresh history; some things held back |
| [11-19](2026-11-19-can-the-gpu-driver-be-fixed.md) | **Can the GPU driver bug be fixed by rebuilding `nvgpu.ko`?** | change | **OPEN**: fixed and installed (clock stays at 510 MHz); one reboot check left |
| [11-19](2026-11-19-switching-between-test-and-production.md) | Can the unit be switched between test and production with one command? | change | **OPEN**: `tools/unit-mode.sh` written; live switch waits for owner |
