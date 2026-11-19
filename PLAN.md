# PLAN: what we are doing now

**Kind:** living · **Last updated:** 2026-11-19

The one file about *today*. Reasons are in the linked journal entries.

## 0. Now: are the resets gone? [journal](journal/2026-10-23-why-does-the-unit-reset.md)

Both logged cut-outs (11-17, 11-18) came from the GPU clock sticking at maximum after Firefox's
start-up or hardware video decoding: ~19.4 W, the supply's limit, for 40-70 min
([journal](journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md)). `gpu-clock-guard` now
fixes the clock within ~10 s, so the unit should stay at ~12-14 W.

| step | what | state |
|---|---|---|
| 1 | button presses at normal load | **done 11-17**: no reset |
| 2 | find the extra load | **done 11-18**: stuck GPU clock; guard installed |
| 3 | run normally, desktop use allowed, logger running; any reset → read `/var/log/vd-power/` and `journalctl -u gpu-clock-guard` | **watching** |
| 4 | a supply with headroom anyway (summer heat in a vehicle) | when convenient |
| 5 | fix the driver bug itself: rebuilt `nvgpu.ko` with NVIDIA's 35.2.1 fix (owner's choice 11-19; [plan and risks](journal/2026-11-19-can-the-gpu-driver-be-fixed.md); [runbook](docs/gpu-driver-fix.md)) | **fixed and installed 11-19 15:06** (fixed driver every boot, automatic fallback; [runbook](docs/gpu-driver-fix.md)). Left: the first reboot hung at the last step (watchdog, ~3 min); owner to reboot once more so we see if it repeats; guard stays |

## 1. Waiting on the owner

| decision | why it matters | notes |
|---|---|---|
| **ownership of the Google Cloud project and the data** | Trifork controls it | legal / commercial; Trifork not responding |
| **leave Trifork's Tailscale network** | their machines can reach the unit | set up our own remote access first; their access is still needed for now |
| **offsite copy** (460 GB mirror + 4 GB backup) | everything is on one SSD | **on hold** (owner, 11-18) |

Settled 11-18 ([journal](journal/2026-11-18-publishing-the-repository.md)): this public repository
with a fresh history; the private one keeps Trifork's history unchanged; no key-rotation request.

## 2. Ready to do, when wanted

- Second unit: GPU fix with `tools/nvgpu-fix/perm/install-nvgpu-fix.sh` (checks it is identical first; [runbook](docs/gpu-driver-fix.md#installing-on-another-unit)).
- `tools/unit-mode.sh production|test`: written and checked read-only (status, compose edits on a copy); the live switch, which restarts recording, not yet run (owner's go).

- Find out why the 11-17 09:10 press recorded 3 frames instead of 7.
- Find out why the frame rate varies since the 11-18 reboots (1.7-2.7 fps; 1.47 before).
- Fix the camera-setup check so the log stops claiming cameras are configured when they are absent (defects 1, 2, 8). [journal](journal/2026-09-08-what-is-wrong-in-the-code.md)
- Restrict `/var/secrets/*` to mode `640`. [journal](journal/2026-09-08-what-is-wrong-in-the-code.md)
- GPS antenna to a window. [journal](journal/2026-10-23-why-does-the-gps-have-no-fix.md)
- Disable `updates.service`: its token is revoked and it can no longer do anything useful.
- A fresh stakeholder brief: the September one is in `archive/`.

## 3. Running

- `gpu-clock-guard.service`: keeps the GPU clock under the power-mode cap. Keep it.
- `vd-power-log.service`: the input-power logger, until the reset question is closed.

## 4. Deliberately not doing

- **Driving with the indoor exposure**: switch first: `bash tools/unit-mode.sh production` ([operations](docs/operations.md#test-or-production-ready-to-drive)).
- **Re-enabling uploads**: they would go to Trifork's bucket. Settle ownership first, or point them at our own bucket.
- **Publishing Trifork's history, their framework or the cloud manifests.**
