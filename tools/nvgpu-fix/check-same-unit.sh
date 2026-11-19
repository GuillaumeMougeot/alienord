#!/bin/bash
# alienord: is this unit identical to bluemar-bio-xnx-2, for which nvgpu-fixed.ko was built?
#     bash check-same-unit.sh          (no root needed; changes nothing)
# Prints one line per check and "SAME" or "DIFFERENT" at the end (exit 0 / 1).
# A different kernel would make the fixed module refuse to load (harmless: the loader then loads the
# original), but install only on a unit that passes every check.
ok=1
chk() { # name, actual, expected
    if [ "$2" = "$3" ]; then echo "  ok        $1"; else echo "  DIFFERENT $1"; echo "            here:     $2"; echo "            expected: $3"; ok=0; fi
}
sha() { sha256sum < "$1" 2>/dev/null | cut -d' ' -f1; }
M=/lib/modules/5.10.104-tegra
echo "checking this unit ($(hostname)) against bluemar-bio-xnx-2:"
chk "model"                    "$(tr -d '\0' < /proc/device-tree/model | sed 's/ *$//')" "ThinkEdge SE70 (NVIDIA Jetson Xavier NX)"
chk "running kernel"           "$(cat /proc/version)" "Linux version 5.10.104-tegra (root@ubuntu) (aarch64-buildroot-linux-gnu-gcc.br_real (Buildroot 2020.08) 9.3.0, GNU ld (GNU Binutils) 2.33.1) #1 SMP PREEMPT Fri Sep 22 14:53:43 CST 2023"
chk "kernel configuration"     "$(zcat /proc/config.gz | sha256sum | cut -d' ' -f1)" "9f3b7ee5ab149c4172f89c1b682c0b66023ebb8fd03fc58c78a7618657db8947"
chk "L4T release"              "$(head -1 /etc/nv_tegra_release)" "# R35 (release), REVISION: 1.0, GCID: 31250864, BOARD: t186ref, EABI: aarch64, DATE: Thu Aug 11 03:40:29 UTC 2022"
chk "Lenovo image"             "$(head -1 /etc/se70ota_release 2>/dev/null)" "R35.1.0-0.0.1"
chk "kernel image /boot/Image" "$(sha /boot/Image)" "8bfa1c5c159f702395a6767c0d737ff9eb912eab2ada332bd04ce89781a7ffff"
chk "original GPU driver"      "$(sha $M/kernel/drivers/gpu/nvgpu/nvgpu.ko)" "b62d7dec1c2b91804c909a2c18251488e83b009db88369b2e9fa4573bbc13f67"
chk "nvmap driver"             "$(sha $M/kernel/drivers/video/tegra/nvmap/nvmap.ko)" "858621f30a6ca3a5cd3b66ff8d15438fec7f0634996bd54c13d4b5503cc2eb15"
chk "GPU device"               "$(ls /sys/devices/17000000.gv11b/devfreq/ 2>/dev/null)" "17000000.gv11b"
chk "reset-reason file"        "$([ -r /sys/devices/platform/c360000.pmc/reset_reason ] && echo readable)" "readable"
chk "GPU driver loaded at boot by" "$(grep -lx nvgpu /etc/modules-load.d/*.conf 2>/dev/null | head -1)" "/etc/modules-load.d/nv.conf"
if [ $ok = 1 ]; then echo "SAME"; exit 0; else echo "DIFFERENT: do not install the fixed driver on this unit"; exit 1; fi
