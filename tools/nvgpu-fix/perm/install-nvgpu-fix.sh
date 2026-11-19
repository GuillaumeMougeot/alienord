#!/bin/bash
# alienord 2026-11-19: make the rebuilt GPU driver permanent, with automatic fallback to the original.
#     sudo bash /home/xnx/gpu-test/install-nvgpu-fix.sh
# Replaces the one-boot trial. Installs (root-owned):
#   /etc/modprobe.d/nvgpu-fix.conf                   modprobe runs the loader instead of loading nvgpu
#   /usr/local/sbin/nvgpu-fix-load                   the loader (fixed driver unless disabled; see its header)
#   /etc/systemd/system/nvgpu-fix-shutdown.service   records each clean shutdown
#   /var/lib/nvgpu-fix/nvgpu-fixed.ko                the fixed module (sha256 761608e8...f3ec)
# Back to the original by hand: sudo touch /var/lib/nvgpu-fix/disabled && sync && sudo reboot
# Remove everything:            sudo bash /home/xnx/gpu-test/remove-nvgpu-fix.sh
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
P=/home/xnx/gpu-test/perm
FIXED_SRC=/home/xnx/build/nvgpu-fix/fix/nvgpu-fixed.ko
check() { [ "$(sha256sum < "$1" | cut -d' ' -f1)" = "$2" ] || { echo "ABORT: $1 is not the reviewed version"; exit 1; }; }
check "$FIXED_SRC" 761608e899ce995218b26393d223aa7d14ea5c32cb15efd8d1a669bb3242f3ec
check $P/nvgpu-fix-load 11e196c2fdc0d81df5c530c773587ec241cb9f848596aeb6fb2a409ef0425087
check $P/nvgpu-fix.conf 2de728f5dcc68f2e30f0c79e6f4a056d31a35324a707f8f0fb26a1b49e95fb1f
check $P/nvgpu-fix-shutdown.service 889e8c61a01547c34a1150be8ffc1c0353a61c00c276d1179d69820f9e2f126c

# the one-boot trial goes (its log is kept)
rm -f /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load /var/lib/nvgpu-fix/try-next-boot

install -d -o root -g root -m 0755 /var/lib/nvgpu-fix
install -o root -g root -m 0644 "$FIXED_SRC" /var/lib/nvgpu-fix/nvgpu-fixed.ko
install -o root -g root -m 0755 $P/nvgpu-fix-load /usr/local/sbin/nvgpu-fix-load
install -o root -g root -m 0644 $P/nvgpu-fix.conf /etc/modprobe.d/nvgpu-fix.conf
install -o root -g root -m 0644 $P/nvgpu-fix-shutdown.service /etc/systemd/system/nvgpu-fix-shutdown.service
# the fixed driver is already running (trial boot): mark this boot like any fixed-driver boot
[ "$(cat /sys/module/nvgpu/taint)" = O ] && date '+%F %T' > /var/lib/nvgpu-fix/pending
sync
systemctl daemon-reload
systemctl enable --now nvgpu-fix-shutdown.service
sync

echo; echo "checks:"
modprobe -c | grep -q '^install nvgpu /usr/local/sbin/nvgpu-fix-load' && echo "  modprobe rule: OK" || echo "  WARNING: modprobe does not see the rule"
modprobe -c | grep -q 'nvgpu-trial-load' && echo "  WARNING: trial rule still present" || echo "  trial rule removed: OK"
sh -n /usr/local/sbin/nvgpu-fix-load && echo "  loader syntax: OK"
echo "  shutdown service: $(systemctl is-enabled nvgpu-fix-shutdown.service), $(systemctl is-active nvgpu-fix-shutdown.service)"
echo "  running driver: $([ "$(cat /sys/module/nvgpu/taint)" = O ] && echo fixed || echo original)"
ls -l /var/lib/nvgpu-fix/
echo
echo "Installed: every boot now loads the fixed driver. A reboot checks the whole cycle"
echo "(clean shutdown clears 'pending', the next boot loads the fixed driver again)."
read -r -p "Reboot now to check? Type yes: " a
if [ "$a" = yes ]; then echo "rebooting in 5 s"; sleep 5; systemctl reboot; else echo "no reboot; the fixed driver keeps running"; fi
