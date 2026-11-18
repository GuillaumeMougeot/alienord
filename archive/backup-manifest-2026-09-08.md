# VD Biodiversity — recovery backup

**Source device:** bluemar-bio-xnx-2 (Lenovo ThinkEdge SE70 / Jetson Xavier NX, L4T R35.1.0)
**Taken:** 2026-09-08

Purpose: make the system reproducible **without** any access to Trifork's private
GitHub, their Docker registry, or their Google Cloud project.

## Contents

| Path | What it is | Why it matters |
|---|---|---|
| `trifork-core/core/` | Trifork's `trifork-ai-core-tech-stack` **v0.0.1**, 99 `.py` files, extracted from the running container | **The single hard blocker.** Only otherwise available from the private repo `github.com/trifork/ai-core-tech-stack` @ `90c0b92f519beee8069d35a48e56c4fcf9969921`. Provides `Driver`, `Controller`, `PipelineBuilder`, all probe base classes and the domain model. Vendor this into your own repo to cut the dependency permanently. |
| `app-code/bio/` | The deepstream application **as actually deployed** | Differs from the Git repo — this copy has the roadkill model *enabled*. Treat this, not the repo, as the truth about running behaviour. |
| `app-code/gps/`, `app-code/gcs/` | The other two containerised apps | |
| `models/models/` | Model weights: `roadkill/` (yolov8m), `car/` (resnet10 + INT8 calibration), `plant/` (yolov8m-det), plus `models-lock.json` | Otherwise only in `gs://models-bio/`. Retraining is not realistic without their training data, so these weights are effectively irreplaceable. |
| `repo/vd-biodiversity.bundle` | Complete Git history, all branches (`git bundle verify`: "records a complete history") | Restore with `git clone vd-biodiversity.bundle`. HEAD = `ef5a450`. |
| `repo/vd-biodiversity-worktree/` | Working-tree copy of `/opt/code/vd-biodiversity` | **Token has been stripped** from `.git/config` — see Credentials below. |
| `host-config/opt-apps/` | All of `/opt/apps` — service scripts, compose files, device YAML, and the two **vendor binaries** `se70_tool` (SE70 digital I/O and LED) and `AutoIPConfigTool` (Daheng camera IP setup) | Those binaries cannot be re-obtained now that the project is discontinued. |
| `host-config/systemd/` | The six unit files | |
| `host-config/fstab` | Data-disk mount by UUID | |
| `host-config/*.txt` | Network connections, IP layout, image IDs/digests, `pip freeze` from inside the deepstream container | Needed to reconstruct the Python environment. |
| `docker-images/*.tar.gz` | `docker save` of all three images | Restore with `gunzip -c <f>.tar.gz \| docker load`. Not pullable without their registry. |

## What is deliberately NOT here: credentials

No secrets were copied into this archive. Two live credentials exist on the device, both
**world-readable (`-rw-r--r--`)**, which is itself a finding worth fixing:

| Credential | Location on device | Grants |
|---|---|---|
| GitHub personal access token (`ghp_…`) | `/var/secrets/bot.env`, and in plaintext inside the remote URL in `/opt/code/vd-biodiversity/.git/config` | Access to Trifork's private GitHub repos |
| GCP service-account key | `/var/secrets/nordfou-biodiversity-2cd0fb3af162.json` | `bot-service-account@nordfou-biodiversity.iam.gserviceaccount.com` — read/write on all buckets in project `nordfou-biodiversity`, including every image the fleet has ever captured |

Recommended handling: copy both into a password manager, not into a backup archive; then
tighten the file modes on the device (`chmod 640`, correct group). The GitHub token should be
reported to Trifork for rotation **after** you have finished mirroring anything you need from
their GitHub — the bundle here already contains the full `vd-biodiversity` history, so the only
remaining reason to keep it is `ai-core-tech-stack`, and `trifork-core/` above already covers that.

## Restoring onto a fresh device

1. Flash and configure the Jetson per `docs/prepare-fresh-jetson-xnx.md` in the repo.
2. `docker load` the three images from `docker-images/`.
3. Recreate `/opt/apps` from `host-config/opt-apps/`, and the units from `host-config/systemd/`.
4. Recreate `/var/shared/{heartbeat,pid,logs}`, `/var/secrets`, `/media/data/{images,meta,recordings}`
   and the users/groups (`app`, `uploader`, `monitoring`; groups `shared`, `apps`, `gcs`, `fleet`) —
   see `scripts/setup-xnx.sh` in the repo.
5. Supply your own credentials in `/var/secrets`.
6. Create the device YAML in `/opt/apps/deepstream/devices/<hostname>.yaml` mapping the two camera
   serial numbers to `REAR_CAMERA` / `SIDE_CAMERA`.
7. Mount the data disk by UUID per `host-config/fstab`.

Steps 2–3 do not require Trifork. Rebuilding the *image* from source additionally requires
`trifork-core/` (included) plus a `dataclass-wizard` fork at `github.com/cgrtrifork/dataclass-wizard`
@ `3adedbec5afd04d82cbc5f52e9daf80c709961f3` — **not yet mirrored, worth doing**; the built copy is
in `host-config/deepstream-pip-freeze.txt` as `dataclass-wizard 0.22.2`, and the installed package
can be pulled from the container the same way `core` was.

## Next step

This staging directory is **on the device it protects**, which is not yet a backup. Copy it off:

```bash
tar -czf vd-biodiversity-backup-20260908.tar.gz -C ~/backup vd-biodiversity-20260908
# then scp/rsync to storage you control, plus one offsite copy
```
