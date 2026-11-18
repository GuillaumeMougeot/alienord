# Can uploading and deleting be switched off for debugging?

**Kind:** change · **Status:** RESOLVED (2026-10-23): yes, via `/opt/apps/gcs/control/upload.conf`.
Building it exposed a bug: **a failed upload deleted the file**. Fixed. Uploads have been off since.

## The bug

`GCS.upload_blob()` caught every exception, logged it and returned normally; the uploader then ran
`os.remove()` regardless. With no network, or a revoked key, every captured file would have been
deleted without reaching the cloud. Now `upload_blob()` returns `True`/`False`, and a failed file stays
for the next cycle.

## The switches

`UPLOAD_ENABLED` and `DELETE_AFTER_UPLOAD`, read at the start of every cycle, so no restart is needed.
With deletion off, an uploaded file is moved to `/media/data/uploaded/<folder>/`, which avoids
uploading it again every 15 min. Usage: [`../docs/operations.md`](../docs/operations.md#upload-switches).

## How it is wired

The deployed app code was copied out of the `gcs` image to `/opt/apps/gcs/app-override/`, and three
files were changed: `uploader.py`, `cloud/adapters/gcs.py`, and one line in `main.py` that logs the
mode. It is mounted over the image's copy, together with `/opt/apps/gcs/control/`. The control folder
is mounted as a directory because editors that replace a file would break a single-file mount.
Original compose: `docker-compose.yaml.orig-20261023`.

## Verification

Eight unit tests in a throwaway container with a fake cloud: default, upload off, keep-local, failure
with delete on and off, parsing, live re-read, and the adapter's return value. All pass. In
production, uploads off kept 16 files in place. The keep-local path has not run in production,
because that needs a real upload.
