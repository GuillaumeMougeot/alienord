#!/bin/bash
# alienord: remove the rebuilt GPU driver setup completely; every boot then loads the original.
#     sudo bash tools/nvgpu-fix/perm/remove-nvgpu-fix.sh
# The driver already running stays until the next reboot. The loader's log and state are kept in
# /root/nvgpu-fix-saved/.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
systemctl disable --now nvgpu-fix-shutdown.service 2>/dev/null
rm -f /etc/systemd/system/nvgpu-fix-shutdown.service /etc/modprobe.d/nvgpu-fix.conf /usr/local/sbin/nvgpu-fix-load
rm -f /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load
systemctl daemon-reload
mkdir -p /root/nvgpu-fix-saved
cp -a /var/lib/nvgpu-fix/*.log /var/lib/nvgpu-fix/disabled /root/nvgpu-fix-saved/ 2>/dev/null
rm -rf /var/lib/nvgpu-fix
sync
modprobe -c | grep -q '^install nvgpu' && echo "WARNING: an nvgpu install rule is still there" || echo "removed: the next boot loads the original driver (logs kept in /root/nvgpu-fix-saved/)"
