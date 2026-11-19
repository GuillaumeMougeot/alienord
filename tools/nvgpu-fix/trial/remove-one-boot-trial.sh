#!/bin/bash
# alienord 2026-11-19: remove the one-boot trial completely (the original driver loads as before).
#     sudo bash /home/xnx/gpu-test/remove-one-boot-trial.sh
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
[ -e /var/lib/nvgpu-fix/trial.log ] && cp /var/lib/nvgpu-fix/trial.log /home/xnx/gpu-test/trial.log && chown xnx:xnx /home/xnx/gpu-test/trial.log
rm -f /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load
rm -rf /var/lib/nvgpu-fix
sync
modprobe -c | grep -q '^install nvgpu' && echo "WARNING: an nvgpu install rule is still there" || echo "removed; nothing changes for the running system, and every boot loads the original driver"
