#!/bin/bash
# alienord 2026-11-19: install the one-boot trial of the rebuilt GPU driver, then (if you say yes)
# arm it and reboot.       sudo bash /home/xnx/gpu-test/install-one-boot-trial.sh
# Installs three files (root-owned); normal boots keep loading the original driver.
#   /etc/modprobe.d/nvgpu-fix-trial.conf   /usr/local/sbin/nvgpu-trial-load   /var/lib/nvgpu-fix/nvgpu-fixed.ko
# Undo at any time: sudo bash /home/xnx/gpu-test/remove-one-boot-trial.sh
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
T=/home/xnx/gpu-test/trial
FIXED_SRC=/home/xnx/build/nvgpu-fix/fix/nvgpu-fixed.ko
check() { [ "$(sha256sum < "$1" | cut -d' ' -f1)" = "$2" ] || { echo "ABORT: $1 is not the reviewed version"; exit 1; }; }
check "$FIXED_SRC" 761608e899ce995218b26393d223aa7d14ea5c32cb15efd8d1a669bb3242f3ec
check $T/nvgpu-trial-load 35f7000a88b0849d56afd6f5f3990597596334d19b61c63589d909c7607b6c39
check $T/nvgpu-fix-trial.conf 75a82e6efdd716ec069b3c37cf9ba33cbeab7b95c19c90614c13bc116d976f15
[ -e /etc/modprobe.d/nvgpu-fix-trial.conf ] && echo "(already installed: refreshing)"

install -d -o root -g root -m 0755 /var/lib/nvgpu-fix
install -o root -g root -m 0644 "$FIXED_SRC" /var/lib/nvgpu-fix/nvgpu-fixed.ko
install -o root -g root -m 0755 $T/nvgpu-trial-load /usr/local/sbin/nvgpu-trial-load
install -o root -g root -m 0644 $T/nvgpu-fix-trial.conf /etc/modprobe.d/nvgpu-fix-trial.conf
sync

echo "installed:"; ls -l /etc/modprobe.d/nvgpu-fix-trial.conf /usr/local/sbin/nvgpu-trial-load /var/lib/nvgpu-fix/
modprobe -c | grep -q '^install nvgpu /usr/local/sbin/nvgpu-trial-load' && echo "modprobe sees the rule: OK" || { echo "WARNING: modprobe does not see the rule; not arming"; exit 1; }
sh -n /usr/local/sbin/nvgpu-trial-load && echo "loader syntax: OK"
echo
echo "Arming = the NEXT boot only uses the fixed driver; if it crashes, the unit resets after 10 s"
echo "and comes back on the original by itself (screen black for ~1 min, then normal boot)."
read -r -p "Arm the trial and reboot now? Type yes: " a
if [ "$a" = yes ]; then
    touch /var/lib/nvgpu-fix/try-next-boot; sync
    echo "armed; rebooting in 5 s"; sleep 5; systemctl reboot
else
    echo "not armed. Normal boots load the original driver. To arm later:"
    echo "  sudo touch /var/lib/nvgpu-fix/try-next-boot && sync && sudo reboot"
fi
