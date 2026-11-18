# Why do the logs grow without bound, and why is the history lost at boot?

**Kind:** change · **Status:** RESOLVED (2026-10-23), except the container logs (in [`../PLAN.md`](../PLAN.md)).

- `logrotate` was **not installed**: `/var/log/syslog` was 4.0 GB and `/var/shared/logs` 527 MB. The
  owner installed it, and its default rule now rotates syslog. A rule for the app logs is in
  `/etc/logrotate.d/vd-biodiversity`: daily or above 50 MB, 14 compressed copies, `copytruncate`
  (the apps keep the files open), and `su root shared` (the folder is group-writable). Mirror:
  [`../device/bluemar-bio-xnx-2/logrotate/`](../device/README.md).
- The journal was **volatile**, which is why the six-week outage could not be explained. It is
  persistent since 2026-10-23 14:46. Creating `/var/log/journal` alone left it unreadable to the
  `adm` group; `systemd-tmpfiles --create --prefix /var/log/journal` fixed the permissions.
- Before rotation began, the logs were archived to `~/backup/logs-20261023/` (39 MB app, 319 MB
  system). They hold the only record of the outage, and the syslog contains the (revoked) GitHub
  token six times.
- Still unbounded: the containers' own logs (deepstream 1.2 GB, gps 641 MB, since 2026-09-08). Fix:
  a `logging:` size limit in each compose file, which recreates the containers.
