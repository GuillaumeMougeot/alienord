# Can the containers' own logs be capped?

**Kind:** change · **Status:** RESOLVED (2026-11-18): yes. Each container's log is now limited to
3 × 10 MB.

Docker kept each container's output in one unbounded JSON file. The gps container's had reached
655 MB since 2025-03-17 (one `Saving new GPS coordinates` line per second); the deepstream one had
reached 1.2 GB before it was recreated on 11-17. Disk space was never the problem (200 GB free); the
problem was that `docker logs --since` reads the whole file
([11-16](2026-11-16-why-is-the-led-yellow-when-frames-flow.md)).

**Change:** in each of `/opt/apps/{deepstream,gps,gcs}/docker-compose.yaml`, a `logging:` block
(`json-file`, `max-size: "10m"`, `max-file: "3"`), originals kept as
`docker-compose.yaml.before-logging-20261118`. The containers were recreated one at a time (gcs, gps,
deepstream), and each confirmed running with the new limit. Recreation discarded their old logs; the
same output is in the journal and syslog. Health afterwards: all heartbeats fresh, exposure override
still mounted, uploads still off. Undo: [`../docs/reverting.md`](../docs/reverting.md#container-log-limits-2026-11-18).
