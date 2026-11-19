#!/bin/bash
# alienord 2026-11-19: remove the rebuilt GPU driver setup completely; every boot loads the original.
#     sudo bash /home/xnx/gpu-test/remove-nvgpu-fix.sh
# The driver already running stays until the next reboot.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
systemctl disable --now nvgpu-fix-shutdown.service 2>/dev/null
rm -f /etc/systemd/system/nvgpu-fix-shutdown.service /etc/modprobe.d/nvgpu-fix.conf /usr/local/sbin/nvgpu-fix-load
rm -f /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load
systemctl daemon-reload
mkdir -p /home/xnx/gpu-test/saved-state
cp -a /var/lib/nvgpu-fix/*.log /var/lib/nvgpu-fix/disabled /home/xnx/gpu-test/saved-state/ 2>/dev/null
chown -R xnx:xnx /home/xnx/gpu-test/saved-state
rm -rf /var/lib/nvgpu-fix
sync
modprobe -c | grep -q '^install nvgpu' && echo "WARNING: an nvgpu install rule is still there" || echo "removed: the next boot loads the original driver (logs kept in ~/gpu-test/saved-state)"
