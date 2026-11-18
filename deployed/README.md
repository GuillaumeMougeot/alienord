# Code as deployed

Copied on 2026-09-08 from inside the three running containers (`/workspaces/...`). This is what the unit
actually runs, and it **differs from `main`**: for example, `bio/app/pipelines/collection.py` here has
the roadkill model enabled, while `main` has it commented out. Models are excluded (see
`manifests/large-files.md`).

The upload app has since been patched on the unit through a mounted override; that version is in
`device/bluemar-bio-xnx-2/opt-apps/gcs/app-override/`.
