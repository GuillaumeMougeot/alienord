# Where should all the knowledge live?

**Kind:** change · **Status:** RESOLVED (2026-11-17): in this repository, in the owner's note-taking
structure (from `lepinet`): one front door, one status file, one findings file, `docs/` for current
reference, this journal, and `archive/` for what is superseded.

- 2026-11-16: repository created from the Git bundle, with all 100 of Trifork's branches as
  `trifork/*`, plus `vendor/`, `deployed/`, `device/` and the handover documents. Kept local; a
  `pre-push` hook blocks pushes ([why](2026-11-16-credentials-in-trifork-history.md)).
- 2026-11-17: the 1,371-line handbook and the separate files under `~/Documents` were split into the
  layers above. The handbook is kept whole in [`../archive/`](../archive/README.md). Trifork's own
  docs and README moved to [`../docs/trifork/`](../docs/trifork/README.md).
