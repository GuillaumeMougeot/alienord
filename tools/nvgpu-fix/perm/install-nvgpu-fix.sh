#!/bin/bash
# alienord: install the rebuilt GPU driver (NVIDIA's 35.2.1 clock fix for L4T 35.1) on a Lenovo SE70
# identical to bluemar-bio-xnx-2, with automatic fallback to the original driver.
#     sudo bash tools/nvgpu-fix/perm/install-nvgpu-fix.sh        (from a clone of the repository)
# Checks the unit is identical (../check-same-unit.sh) and the files are the tested ones, then
# installs (root-owned):
#   /etc/modprobe.d/nvgpu-fix.conf                   modprobe runs the loader instead of loading nvgpu
#   /usr/local/sbin/nvgpu-fix-load                   the loader (rules: docs/gpu-driver-fix.md)
#   /etc/systemd/system/nvgpu-fix-shutdown.service   records each clean shutdown
#   /var/lib/nvgpu-fix/nvgpu-fixed.ko                the fixed module
# Takes effect at the next boot (never reload nvgpu on a running system: it crashes the kernel).
# Back to the original: sudo touch /var/lib/nvgpu-fix/disabled && sync && sudo reboot
# Remove everything:    sudo bash tools/nvgpu-fix/perm/remove-nvgpu-fix.sh
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
P=$(dirname "$(readlink -f "$0")")
bash $P/../check-same-unit.sh || { echo "ABORT: nothing installed"; exit 1; }
check() { [ "$(sha256sum < "$1" | cut -d' ' -f1)" = "$2" ] || { echo "ABORT: $1 is not the tested version"; exit 1; }; }
check $P/nvgpu-fixed.ko 761608e899ce995218b26393d223aa7d14ea5c32cb15efd8d1a669bb3242f3ec
check $P/nvgpu-fix-load 11e196c2fdc0d81df5c530c773587ec241cb9f848596aeb6fb2a409ef0425087
check $P/nvgpu-fix.conf 2de728f5dcc68f2e30f0c79e6f4a056d31a35324a707f8f0fb26a1b49e95fb1f
check $P/nvgpu-fix-shutdown.service 889e8c61a01547c34a1150be8ffc1c0353a61c00c276d1179d69820f9e2f126c

# the one-boot trial, if present, goes
rm -f /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load /var/lib/nvgpu-fix/try-next-boot

install -d -o root -g root -m 0755 /var/lib/nvgpu-fix
install -o root -g root -m 0644 $P/nvgpu-fixed.ko /var/lib/nvgpu-fix/nvgpu-fixed.ko
install -o root -g root -m 0755 $P/nvgpu-fix-load /usr/local/sbin/nvgpu-fix-load
install -o root -g root -m 0644 $P/nvgpu-fix.conf /etc/modprobe.d/nvgpu-fix.conf
install -o root -g root -m 0644 $P/nvgpu-fix-shutdown.service /etc/systemd/system/nvgpu-fix-shutdown.service
# if the fixed driver is already running, mark this boot like any fixed-driver boot
[ "$(cat /sys/module/nvgpu/taint)" = O ] && date '+%F %T' > /var/lib/nvgpu-fix/pending
sync
systemctl daemon-reload
systemctl enable --now nvgpu-fix-shutdown.service
sync

echo; echo "checks:"
modprobe -c | grep -q '^install nvgpu /usr/local/sbin/nvgpu-fix-load' && echo "  modprobe rule: OK" || echo "  WARNING: modprobe does not see the rule"
sh -n /usr/local/sbin/nvgpu-fix-load && echo "  loader syntax: OK"
echo "  shutdown service: $(systemctl is-enabled nvgpu-fix-shutdown.service), $(systemctl is-active nvgpu-fix-shutdown.service)"
echo "  running driver now: $([ "$(cat /sys/module/nvgpu/taint)" = O ] && echo fixed || echo original)"
echo
echo "Installed: from the next boot on, the fixed driver loads (if it ever crashes, the unit resets and"
echo "switches back to the original by itself). After the reboot, check:"
echo "  cat /sys/module/nvgpu/taint     (O = fixed)      tail -2 /var/lib/nvgpu-fix/boot.log"
read -r -p "Reboot now? Type yes: " a
if [ "$a" = yes ]; then echo "rebooting in 5 s"; sleep 5; systemctl reboot; else echo "no reboot; the fix starts at the next boot"; fi
