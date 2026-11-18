# What would we lose if Trifork's access disappeared?

**Kind:** investigation · **Status:** RESOLVED (2026-09-08, data part 2026-11-16): two private build
dependencies, the container images, the code and all the data were reachable only through Trifork. All
are now secured locally. Current table: [`../docs/dependencies.md`](../docs/dependencies.md).

## What was found

- The app imports `core`, Trifork's private `trifork-ai-core-tech-stack` v0.0.1, pinned to commit
  `90c0b92f` of `github.com/trifork/ai-core-tech-stack`. It holds the main loop, pipeline builder and
  probe base classes; without it the code cannot be rebuilt. It ships as plain `.py` inside the image.
- A fork of `dataclass-wizard` on a Trifork employee's GitHub.
- The three container images exist only in Trifork's Artifact Registry.
- The code is on Trifork's GitHub, cloned with a bot token kept in plaintext.
- All captured data goes to Trifork's Google Cloud project.
- The unit is on Trifork's Tailscale network; their staff machines are peers.

## What was done (2026-09-08)

A recovery backup, at `/media/data/backup/vd-biodiversity-20260908/` and `~/backup/`: `core` (99
files) and `dataclass-wizard` extracted from the container, the three images saved (`gzip -t` and
`manifest.json` verified), a full-history Git bundle (`bundle verify`: complete), the models, `/opt/apps`
including the vendor tools `se70_tool` and `AutoIPConfigTool`, and the systemd units. 4,331,426,154
bytes, byte-identical on both disks. No credentials were included.

## Since then

- 2026-10-23: Trifork's GitHub token was found **revoked**; the bundle is the only copy of the history.
- 2026-11-16: every cloud bucket copied locally; see [retrieving all cloud data](2026-11-16-retrieving-all-cloud-data.md).
