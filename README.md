# VD Biodiversity

A roadside survey unit: a Jetson Xavier NX in a vehicle box, with two cameras and a GPS. While
driving above 80 km/h it detects dead animals (rear camera) and seven invasive plant species (side
camera), saves GPS-tagged images and uploads them to Google Cloud; a green button records a 5-second
burst. **Trifork** built it and has discontinued the project. Since September 2026 it has been
reverse-engineered on unit `bluemar-bio-xnx-2`, and this repository holds everything known about it.

## 1. Where things stand (2026-11-18)

- **Working:** cameras, the detection pipeline (~1.4 fps per camera), recordings, and the yellow LED,
  which now means "not capturing". Uploads are **off**: data stays on the unit.
- **All cloud data is secured locally:** ~460 GB from seven buckets, verified, on the unit's SSD.
  There is **no offsite copy** (on hold).
- **The resets are explained and guarded against:** video decoding or a browser start left the GPU
  clock at maximum, which put the unit at its power supply's limit (~19 W) until the supply cut
  out. A guard service now fixes the clock within ~10 s ([journal](journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md)).
  Being watched: [PLAN](PLAN.md).
- **The cameras are set for indoor tests** (exposure 100 ms): [revert before driving](docs/reverting.md).
- **This repository is public, with a fresh history.** Trifork's full history (it contains a live
  key), their internal framework and the cloud manifests stay in a private local repository:
  [what and why](journal/2026-11-18-publishing-the-repository.md).

## 2. What to read

| time | read |
|---|---|
| **5 minutes** | this page and [`PLAN.md`](PLAN.md) |
| **20 minutes** | [`FINDINGS.md`](FINDINGS.md): everything established, and every change made to the unit |
| **to use the unit** | [`docs/operations.md`](docs/operations.md) |
| **to understand or change it** | [`docs/system.md`](docs/system.md), [`docs/configuration.md`](docs/configuration.md) |
| **data, backups, Trifork** | [`docs/data-and-backups.md`](docs/data-and-backups.md), [`docs/dependencies.md`](docs/dependencies.md) |
| **why something is the way it is** | [`journal/README.md`](journal/README.md): one entry per question |

[`CLAUDE.md`](CLAUDE.md) is the AI agent's operating manual; humans can skip it.

## 3. The map

| part | what | where |
|---|---|---|
| **notes** | status, findings, reference docs, journal | `PLAN.md`, `FINDINGS.md`, `docs/`, `journal/` |
| **Trifork's code** | the original repository's `main` as handed over (its history is kept private) | `bio/`, `gps/`, `gcs/`, `camera/`, `deepstream-monitoring/`, `updates/`, `scripts/`, `Search/`, `training/` |
| **Trifork's docs** | flashing, hardware setup, troubleshooting | `docs/trifork/` |
| **recovered** | the `dataclass-wizard` fork; Trifork's framework, needed to rebuild, is kept private | `vendor/` |
| **as running** | the code inside the containers, which differs from `main` | `deployed/` |
| **the unit** | its host configuration, including every change made | `device/` |
| **checksums** | models, images (the cloud-object lists are kept private) | `manifests/` |
| **guard rail** | the credential check run before every commit and push | `tools/` |
| **GPU driver fix** | rebuilt `nvgpu.ko` with NVIDIA's 35.2.1 clock fix: patch, build and verification tools; installer for identical units (`perm/`) | `tools/nvgpu-fix/` |
| **reports** | plain-language summaries to pass on | `reports/` |
| **superseded** | the old handbook and brief | `archive/` |

## 4. Conventions

- **Logs are in UTC**, one to two hours behind the wall clock. Journal entries use local time unless marked.
- **No credentials in Git**, ever; they live in `/var/secrets/` on the unit.
- **Every commit and push is checked for credentials** by `tools/check-secrets.sh`; after cloning, run
  `tools/install-hooks.sh`.
- Large files (models, images, the 460 GB mirror) stay out of Git; `manifests/` has their checksums.
