# Can all the project's cloud data be copied locally?

**Kind:** change · **Status:** RESOLVED (2026-11-16): yes. Seven buckets, ~460 GB, copied to the SSD
and verified in 3.5 h.

Nobody knew where the data was, and Trifork controls the project. While the unit's key still works,
everything was copied before anything could cut access.

## How

- **Network:** the office cable on `eth2` was losing to the 4G route (metric 100 vs 101).
  `nmcli con modify "Wired connection 3" ipv4.route-metric 50 ipv6.route-metric 50` made it preferred:
  ~42 MiB/s against ~4 MiB/s on 4G. The 4G remains the fallback.
- **The job** (`~/gcs-archive-job/`, mirrored in [`../device/`](../device/README.md)), a user
  service with lingering enabled so it survives power cuts. For each bucket: a manifest (name, size,
  crc32c, md5), `gcloud storage rsync` (hash-checked, resumable), then a check of every object against
  the manifest. A bucket counts as complete only when that check passes.

## Results

| Bucket | Objects | GB |
|---|---|---|
| data-biodiversity | 288,699 | 232.39 |
| artifacts-bio | 6,992 | 212.66 |
| data-roadkill | 2,124 | 12.70 |
| models-bio | 15 | 1.23 |
| vd-website | 136 | 0.46 |
| data-bio | 379 | 0.10 |
| gcf-v2-sources-… (deployed function code) | 2 + 2 older versions | 0.02 |

## Surprises

- **Faster than estimated** (3.5 h, not 5-7): gcloud downloads large files in parallel slices.
- **A versioned bucket:** the function-code bucket keeps old generations under the same name. rsync
  took only the current ones, and the check counted the old ones as present, a gap in the checker. The
  old generations were fetched by number (`function-source.<date>.gen-<n>.zip`), and `verify.py` now
  fails when a name repeats. The six data buckets have no versions.
- **The progress display** showed 2.1 GB for every large bucket: mawk's `printf "%d"` caps at 2³¹.
  Display only; fixed.
- **No reset under 3.5 h of heavy load**, which bears on [the reset question](2026-10-23-why-does-the-unit-reset.md).
  The rear camera's stream dropped twice (15:27, 16:15) and recovered in about a minute, probably CPU
  starvation of its network stream.
- **Not retrievable:** the Firestore index (no permission). It is derived from `meta/*.json`.
