# Undoing every change made to the unit

One place for every revert command. Newest first. Each change and its reason:
[`../FINDINGS.md`](../FINDINGS.md) §2. Commands without `sudo` run as `xnx`.

**Restarting deepstream** applies a compose-file change and recreates the container (~30 s):
`docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)`.

## Rebuilt GPU driver (`nvgpu.ko`, 2026-11-19)

Back to the original for a while: `sudo touch /var/lib/nvgpu-fix/disabled && sync && sudo reboot`.
Remove everything: `sudo bash /home/xnx/gpu-test/remove-nvgpu-fix.sh`, or just
`sudo rm /etc/modprobe.d/nvgpu-fix.conf && sync && sudo reboot`. Every case, including the NVMe on
another PC: [gpu-driver-fix.md](gpu-driver-fix.md).

## GPU clock guard (2026-11-18)

```bash
sudo systemctl disable --now gpu-clock-guard
sudo rm /etc/systemd/system/gpu-clock-guard.service && sudo systemctl daemon-reload
rm -r /opt/apps/gpu-clock-guard
```

Without it, a browser start or hardware video decoding leaves the GPU at 1109 MHz until reboot
(+8 W). Manual fix then: `D=/sys/devices/17000000.gv11b/devfreq/17000000.gv11b; echo 408000000 |
sudo tee $D/max_freq; echo 510000000 | sudo tee $D/max_freq`.

## Container log limits (2026-11-18)

```bash
for app in deepstream gps gcs; do sed -i '/^    logging:/,/max-file/d' /opt/apps/$app/docker-compose.yaml; done
docker stop gcs; docker stop gps                                        # systemd recreates them
docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)
```

Each container's log then grows without limit again.

## Indoor camera exposure (2026-11-17)

Both cameras' `AutoExposureTimeMax` raised to 100000 µs = 100 ms (from rear 1000, side 200) through
a config override. **Revert before driving**: at 80 km/h, 100 ms is over two metres of motion blur.

```bash
sed -i '\#config-override/config.yaml:/workspaces#d' /opt/apps/deepstream/docker-compose.yaml
docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)
# check, ~30 s later: should show 1000 and 200
docker exec deepstream_app grep AutoExposureTimeMax /workspaces/vd-biodiversity/bio/configs/config.yaml
```

The override file stays in `/opt/apps/deepstream/config-override/config.yaml`, beside the image's
original `config.yaml.pristine`; it does nothing once unmounted.

## Office network preferred over 4G (2026-11-16)

```bash
nmcli con modify "Wired connection 3" ipv4.route-metric -1 ipv6.route-metric -1 && nmcli device reapply eth2
```

## Input-power logger (2026-11-16)

```bash
sudo systemctl disable --now vd-power-log && sudo rm /etc/systemd/system/vd-power-log.service && sudo systemctl daemon-reload
```

Its logs in `/var/log/vd-power/` stay. Keep it running until the reset question is closed.

## Cloud mirror job (2026-11-16)

```bash
systemctl --user disable gcs-archive
loginctl disable-linger xnx
```

The mirrored data in `/media/data/gcs-archive/` is not touched.

## LED logic (2026-10-23, revised 2026-11-16)

```bash
cd /opt/apps/deepstream-monitoring
cp launch.sh.prev-20261116 launch.sh      # the 10-23 version (slow log query; can show yellow while frames flow)
cp launch.sh.orig-20261023 launch.sh      # or Trifork's original: heartbeat only, blind to crash loops
sudo systemctl restart deepstream-monitoring
```

## Uploads off, and the upload switches (2026-10-23)

Re-enable uploads but keep the fix (a failed upload keeps its file). **Uploads go to Trifork's bucket.**

```bash
sed -i 's/^UPLOAD_ENABLED=.*/UPLOAD_ENABLED=true/' /opt/apps/gcs/control/upload.conf
docker stop gcs        # systemd restarts it and it uploads at once
```

Or return to Trifork's original uploader, which **deletes files even when the upload fails**:

```bash
cp /opt/apps/gcs/docker-compose.yaml.orig-20261023 /opt/apps/gcs/docker-compose.yaml
docker stop gcs
```

## App-log rotation and the persistent journal (2026-10-23, run by the owner)

```bash
sudo rm /etc/logrotate.d/vd-biodiversity                                     # app logs grow without limit again
sudo rm -r /var/log/journal && sudo systemctl restart systemd-journald       # history lost at every boot again; not recommended
```

## Model cache on the SSD (2026-09-08)

Without it every restart takes ~13 minutes again.

```bash
sed -i '\#/media/data/models:/workspaces#d' /opt/apps/deepstream/docker-compose.yaml
docker exec deepstream_app kill -INT $(cat /var/shared/pid/deepstream.pid)
```

## Kept on purpose: data, not settings

Delete these only deliberately: `/media/data/gcs-archive/` (the only local copy of all cloud data),
`/media/data/backup/` and `~/backup/` (the recovery backup and the log archive), `/media/data/models/`
(needed by the model cache), `/var/log/vd-power/`.

**Every original file** is kept beside its replacement: `*.orig-YYYYMMDD` for the first change,
`*.prev-YYYYMMDD` or `*.before-<change>-YYYYMMDD` for later ones.
