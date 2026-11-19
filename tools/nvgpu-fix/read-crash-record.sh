#!/bin/bash
# After a crash and reset: copy the kernel's saved record of the crashed boot (ramoops) to your home.
#     sudo bash /home/xnx/gpu-test/read-crash-record.sh
# Read-only. Run it before the next reboot: the record is kept only across one reset.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
modprobe ramoops; sleep 1
OUT=/home/xnx/gpu-test/crash-$(date +%Y%m%d-%H%M)
mkdir -p $OUT
ls -la /sys/fs/pstore/ | tee $OUT/listing.txt
cp -a /sys/fs/pstore/. $OUT/ 2>/dev/null
chown -R xnx:xnx $OUT; sync
echo "saved to $OUT ($(ls $OUT | wc -l) files). Tell Claude."
