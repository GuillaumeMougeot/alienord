# Where the data is

Status on 2026-11-17. **Nothing below has an offsite copy yet**: everything is on this unit, which
suffers power cuts.

## On the unit

| Path | What | Size |
|---|---|---|
| `/media/data/gcs-archive/<bucket>/` | **the complete copy of every cloud bucket**, verified 2026-11-16 | ~460 GB |
| `/media/data/recordings/`, `images/`, `meta/` | what the pipeline saves now. Uploads are off, so files stay | small |
| `/media/data/models/` | model weights and cached engines, mounted into the container | 0.5 GB |
| `/media/data/backup/vd-biodiversity-20260908/` | recovery backup: images, framework, models, code, unit config ([its README](../archive/backup-manifest-2026-09-08.md)) | 4.1 GB |
| `~/backup/vd-biodiversity-20260908/` | the same backup (staging copy on the boot disk) | 4.1 GB |
| `~/backup/logs-20261023/` | app logs and syslog before rotation began: the only record of the six-week outage. **Contains a revoked GitHub token; do not publish** | 0.36 GB |
| `/var/log/vd-power/` | input-power log | ~10 MB/day |

## In the cloud (Trifork's project), all mirrored

| Bucket | Objects | GB | Content |
|---|---|---|---|
| `data-biodiversity` | 288,699 | 232.4 | images, metadata and recordings from five units (2024-2026); two dataset zips |
| `artifacts-bio` | 6,992 | 212.7 | 207 GB of raw 1080p/4K Swedish field video (Oct 2024), Jetson OS image, app packages, datasets |
| `data-roadkill` | 2,124 | 12.7 | a labelled roadkill dataset |
| `models-bio` | 15 | 1.2 | every model version |
| `vd-website` | 136 | 0.5 | |
| `data-bio` | 379 | 0.1 | older recordings |
| `gcf-v2-sources-…` | 2 + 2 older | 0.02 | the deployed cloud-function code |

Not copied: the Firestore search index (no permission; it is rebuilt from `meta/*.json`). The buckets
are private: anonymous requests are refused.

**Access.** The unit's `gcloud` is signed in as the project's service account
(`bot-service-account@…`, key in `/var/secrets/` and `~/.config/gcloud/`), so `gcloud storage ls|cp|du`
work as `xnx`. That account can write, and very likely delete: be careful with `rm`, `mv` and
deleting `rsync`. **A service account cannot sign in to the web console**
(<https://console.cloud.google.com/storage/browser?project=nordfou-biodiversity>); that needs a person's
Google account granted a role by the project owner. Graphical tools that accept a service-account key
exist (`rclone`, `gcsfuse`, Cyberduck), but the key is Trifork's and leaked; prefer the local mirror.

## Checksums

- cloud manifests (every cloud object's name, size, crc32c and md5): in the private local repository
  `~/vd-biodiversity/manifests/cloud/`, not published, because file names carry GPS positions
- [`../manifests/large-files.md`](../manifests/large-files.md): models, container images, the Git bundle

## Rebuilding a unit

1. Flash the Jetson ([`trifork/prepare-fresh-jetson-xnx.md`](trifork/prepare-fresh-jetson-xnx.md)); mount the SSD.
2. `gunzip -c <image>.tar.gz | docker load` for the three images in the backup.
3. Restore `/opt/apps` and the units from [`../device/bluemar-bio-xnx-2/`](../device/README.md); recreate
   the users and folders as in `scripts/setup-xnx.sh`.
4. Put credentials in `/var/secrets/` (from a password manager; never from Git).
5. Copy the models to `/media/data/models/`; set the camera serials in `devices/<hostname>.yaml`.
