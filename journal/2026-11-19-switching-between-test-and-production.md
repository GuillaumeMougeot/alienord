# Can the unit be switched between test and production with one command?

**Kind:** change · **Status:** OPEN: `tools/unit-mode.sh` written and checked read-only; the live switch (restarts recording) waits for the owner's go.

## The question

The owner (11-19), with a second unit coming: "is there a one line command to switch this device
from a test device to a production ready device?" There was none. Then: "write make-production.sh
and a make-test.sh or one that do both".

## What differs between test and production

From [FINDINGS §2](../FINDINGS.md#2-changes-made-to-the-unit), only one change is test-only: the
**indoor camera exposure** (100 ms on both cameras through a mounted override file;
[11-17](2026-11-17-can-the-cameras-see-indoors.md)). Everything else stays in both modes: models on
the SSD, log caps, the GPU fix and guard, the power logger, the cloud mirror. **Uploads** are off
and stay off in both modes: turning them on is a decision (they go to Trifork's bucket), not a mode.

Trifork's compose files set `ENV=test` everywhere, also on units in the field. In the deployed code
only `ENV=dev` changes anything (`IS_DEV` picks a dev config; `IS_TEST` is never used), so it is
left alone.

## The script

One script, three commands ([operations](../docs/operations.md#test-or-production-ready-to-drive)):
`status` (default), `production`, `test`. No sudo: `xnx` is in the `docker` and `apps` groups, and
`/opt/apps/deepstream/docker-compose.yaml` is group-writable by `apps`.

- `production` deletes the override's mount line (the documented revert), keeps the previous file
  as `docker-compose.yaml.before-unit-mode`, restarts the app (`kill -INT` on its pid, which
  recreates the container), waits for a new container ID and a frame-rate line from it, then runs
  `status`. `test` puts the line back after the models mount, only if the override still holds the
  100 ms values. Re-running the current mode changes nothing.
- `status` reports, each as ok / WARN / FIX: mode (the exposure values the running app actually
  reads, and whether the override is mounted), services, recording (fresh frame-rate line, two
  cameras above 0), GPS (last of "Saving new GPS coordinates" / "NUll Island" in the gps log), GPU
  (fixed driver, or the guard; clock under the cap; power mode 5), data disk below 90 %, clock
  synchronised, uploads. It ends `READY FOR PRODUCTION` or `NOT READY`. GPS without a fix and
  uploads off are warnings: GPS has no fix indoors.

Checks done without changing the unit: `status` here says `TEST` (exposures 100000 / 100000,
override mounted) and NOT READY for that one reason. A first version misread the exposures
(the override file's comments, "was 1000", also hold numbers): fixed by reading only the value
after the colon. Both compose edits, run on a copy: `production` removes exactly the one line;
`test` then restores the file exactly (apart from a final newline the original lacks); both parse
as YAML. Not yet run for real: the switch itself, which restarts recording once.
