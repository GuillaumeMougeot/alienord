# VD Biodiversity — handover

A roadside survey unit: a Jetson Xavier NX in a vehicle box with two GigE cameras and a GPS. While
driving above 80 km/h it detects dead animals (rear camera) and seven invasive plant species (side
camera), saves GPS-tagged images, and uploads them to Google Cloud. A button records a 5-second burst.
Built by **Trifork**, who have discontinued the project; reverse-engineered on unit `bluemar-bio-xnx-2`
from September 2026.

## Read at the depth you need

| Time | Document | For |
|---|---|---|
| 2 min | this page | everyone |
| 5 min | [stakeholder-brief.md](stakeholder-brief.md) (dated 2026-09-08) | non-technical readers |
| reference | [system-handbook.md](system-handbook.md) | anyone running, debugging or changing the system |
| restore | [backup-manifest.md](backup-manifest.md), [large-files-manifest.md](large-files-manifest.md) | rebuilding a unit |

## Where things stand (2026-11-16)

**Working:** cameras, the detection pipeline (~1.4 frames/s per camera), button recordings, GPS
hardware, and the yellow LED, which now means "no frames flowing". **Uploads are switched off**: files
stay on the unit's SSD (switch: `/opt/apps/gcs/control/upload.conf`).

**Open problems, most important first:**

1. **The unit's power supply collapses, and the button triggers it.** Every button press on 23 Oct
   (3 of 3) was followed by a reset within ~30 s, and destroyed its own recording; there were also
   resets with no press. The power chip records input undervoltage every time (handbook Issue 10).
   Inspect the button box wiring, then the supply and its connectors. Until then, avoid the button.
2. **Data and access sit with Trifork.** All project data, ~460 GB across six buckets (232 GB of it
   from the five units), is in Google Cloud project `nordfou-biodiversity`, which they control. **All
   of it was copied to the unit's SSD on 2026-11-16 and verified** (`/media/data/gcs-archive/`,
   handbook §14.7; per-object manifests with checksums in [cloud-manifests/](cloud-manifests/)). That
   copy is not yet offsite. The unit's access key still works; it is also in this repository's history
   (see below). The unit is still on Trifork's Tailscale network.
3. **The GPS antenna sees no satellites** at its current indoor position, so recordings are tagged
   `no_gps` and detection images can't be saved.
4. **Container logs grow without limit** (deepstream 1.2 GB, gps 641 MB).
5. **Backups exist only on this unit.** Copy them offsite, including the cloud mirror once it is complete.

## Short history

| When | What |
|---|---|
| 2026-09-07 | Unit not recording, yellow LED: camera cable moved to the wrong network port; each restart cost 13 min rebuilding AI engines. |
| 2026-09-08 | Recovery backup (incl. Trifork's private framework); engine cache fixed (restart 13 min → 26 s); docs written. |
| 09-08 → 10-20 | Camera side lost power; six weeks of crash loop, no capture. The LED stayed mostly green: a side effect of the faster restarts. |
| 2026-10-23 | Upload switches + fix for a bug that deleted files when uploads failed; LED now checks frame flow; resets traced to power undervoltage; Trifork's GitHub token found revoked. |
| 2026-11-16 | False yellow LED fixed (the frame check choked on a 1.2 GB log damaged by power cuts); this repository created. |

## What is in this repository

| Path | Content |
|---|---|
| everything outside the four folders below | Trifork's repository as recovered: `main`, plus their other 100 branches as `trifork/*` |
| `handover/` | these documents |
| `vendor/` | Trifork's private framework and a forked library, recovered from the running container: without them the code cannot be rebuilt |
| `deployed/` | the application code that actually runs in the containers, which differs from `main` |
| `device/bluemar-bio-xnx-2/` | the unit's live configuration, including every change made during the handover |

Large binaries (models, container images) are not in Git: see [large-files-manifest.md](large-files-manifest.md).

## Before adding a remote: read this

This repository is **local only**, and a `pre-push` hook refuses pushes until the following is decided.
Trifork's history contains credentials that were committed and later deleted, but are still in old commits:

| Credential | Commits | Branches | Still valid? |
|---|---|---|---|
| Google Cloud key for the data bucket, `secrets/nordfou-biodiversity-2cd0fb3af162.json` | 9274ed3 | `trifork/jwme/refactor_makefile` | **yes:** same key ID as the live key on the unit |
| GitHub token, `secrets/.env` | 7111b76, 9274ed3 | `trifork/jwme/refactor_makefile` | unknown |
| Cloud-search database key, `Search/infra/BioDiversityService/cloudfire-biodiversity.json` (+ `_old`) | e519d73, f7a7a52 | **`main`** and four `trifork/allu/*` branches | unknown |
| A 6-character device password | current `docs/flashing_jetson.md` line 32, and history | `main` | unknown |

**Decision 2026-11-16:** no history rewrite, and no request to rotate the key, until the cloud mirror
is complete and verified. *The mirror was completed and verified the same day.* Rotating the key is what would cut access to the data; rewriting this
repository's history would not.

The options before pushing anywhere, even to a private repository:

- **Rewrite the history without those files** (`git filter-repo`). This keeps the commit history; all
  commit IDs change.
- **Push a fresh history** (a single commit of today's files). Simplest; the full history then lives
  only in the offline bundle.

Either way, the Google Cloud key is exposed to anyone who has had access to Trifork's GitHub, so it
should be **rotated** by whoever administers the project. The untouched original history is kept in
the bundle listed in [large-files-manifest.md](large-files-manifest.md).

## Secrets policy

No credentials are stored in this repository's current files. On the unit, they live in
`/var/secrets/`. Keep copies in a password manager, never in Git, not even in a private repository.

## Ownership

The original code was written by Trifork for the project. Confirm the project's rights to it before
publishing anything outside a private repository.
