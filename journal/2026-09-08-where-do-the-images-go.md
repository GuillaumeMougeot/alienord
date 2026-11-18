# Where do the images go?

**Kind:** investigation · **Status:** RESOLVED (2026-10-23): to bucket `data-biodiversity` in
Trifork's Google Cloud project, deleted locally after upload. Uploads are now switched off, and the
whole bucket has been copied locally.

## Findings

- `gcs.service` uploads `/media/data/{images,meta,recordings}` every 15 min to
  `gs://data-biodiversity/<folder>/<device>/` and then deletes the local copy. That is why the 21
  frames from the owner's three presses on 2026-09-08 had vanished: all were in the bucket.
- The project, `nordfou-biodiversity`, sits in a Google Cloud folder that the unit's key cannot read,
  so it belongs to an organisation we cannot see, presumably Trifork's.
- A Cloud Function indexes each upload into Firestore; another serves token-protected searches.
- The bucket is private (anonymous requests get `403`), in `EUROPE-WEST1`, created 2024-02-05.
- 2026-10-23 inventory: the bucket holds all five units' data, ~232 GB. This unit's last detections
  date from 2024-11-01.
- The shipped uploader deleted files even when the upload failed: see
  [the upload switches](2026-10-23-upload-switches-and-the-delete-on-failure-bug.md).

Every bucket in the project was copied locally on 2026-11-16:
[`../docs/data-and-backups.md`](../docs/data-and-backups.md).
