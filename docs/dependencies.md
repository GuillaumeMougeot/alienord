# What still depends on Trifork

Status on 2026-11-17. How each was found and secured: [`../journal/2026-09-08-what-would-we-lose-without-trifork.md`](../journal/2026-09-08-what-would-we-lose-without-trifork.md).

| Dependency | What it blocks | Status |
|---|---|---|
| Framework `trifork-ai-core-tech-stack` (private GitHub) | rebuilding the deepstream image | **secured**: recovered from the container; kept in the private local repository and the recovery backup, not published ([why](../journal/2026-11-18-publishing-the-repository.md)) |
| `dataclass-wizard` fork (Trifork employee's GitHub) | the same | **secured**: in `vendor/` |
| Container images (their Artifact Registry) | setting up a new unit | **secured**: saved archives in the recovery backup |
| Code repository (their GitHub) | updates, history | **secured**: full history in this repository and the bundle. Their token is now revoked, so `updates.service` no longer pulls |
| Google Cloud project `nordfou-biodiversity` | ownership of ~460 GB of data, the search service | **data secured**: everything copied locally 2026-11-16. Ownership unresolved; they control the project |
| Service-account key in `/var/secrets/` | reading and writing that data | still valid. Also leaked in Trifork's Git history ([journal](../journal/2026-11-16-credentials-in-trifork-history.md)); rotation not requested: Trifork does not respond and their access is still needed (owner, 11-18) |
| Model weights (`gs://models-bio`) | retraining, new units | **secured**: in the mirror, the backup and `/media/data/models` |
| Tailscale | remote access, and their access to the unit | the unit is still on **Trifork's tailnet**; their staff machines are peers |
| JFrog Connect | nothing | never installed on this unit |

Ownership: the code was written by Trifork for the project. Confirm the project's rights before
publishing any of it outside a private repository.
