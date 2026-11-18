# Unit configuration

`bluemar-bio-xnx-2/` mirrors the unit's host-side setup as of 2026-11-16:

| Path | On the unit |
|---|---|
| `opt-apps/` | `/opt/apps/`: launch scripts, compose files, the camera-to-role mapping, the vendor tools `se70_tool` and `AutoIPConfigTool` |
| `systemd/` | `/etc/systemd/system/*.service` |
| `logrotate/` | `/etc/logrotate.d/vd-biodiversity` |
| `fstab` | `/etc/fstab` (data-disk mount) |

Changes made during the handover keep the original beside them as `*.orig-YYYYMMDD`; details are in
`FINDINGS.md` §2 and the linked journal entries:

- `opt-apps/deepstream/docker-compose.yaml`: model folder mounted from the SSD, so AI engines are cached (§14.2)
- `opt-apps/gcs/`: upload switches and the delete-on-failure fix (journal 2026-10-23)
- `opt-apps/deepstream-monitoring/launch.sh`: LED means "frames flowing" (journal 2026-10-23, 2026-11-16)
- `opt-apps/power-log/` + `systemd/vd-power-log.service`: input-power logger, installed 2026-11-16 (journal 2026-10-23, reset)
- `gcs-archive-job/` + `systemd-user/gcs-archive.service`: mirror of all cloud buckets to the SSD (journal 2026-11-16, cloud data)
- `network-eth2.txt`: office link preferred over 4G (journal 2026-11-16, cloud data)
- `opt-apps/gpu-clock-guard/` + `systemd/gpu-clock-guard.service`: keeps the GPU clock under the power-mode cap (journal 2026-11-18, GPU clock)
