#!/bin/bash
# Live test of the rebuilt GPU driver (alienord, 2026-11-19). Run from a text console (Ctrl+Alt+F3) or SSH:
#     sudo bash /tmp/gpu-driver-live-test.sh
# The desktop is stopped and restarted. NOTHING is written to /lib/modules or the boot config:
# any reboot brings back the original driver. Runbook: docs/gpu-driver-fix.md in alienord.
#
# Steps: stop everything using the GPU -> unload the original driver -> load the fixed one ->
# re-apply the power mode -> restart everything -> check recording -> repeat the 11-18 decoder
# probe with a kernel trace and check the clock stays at the cap.

SRC=/home/xnx/build/nvgpu-fix/fix/nvgpu-fixed.ko
NEW=/root/nvgpu-fixed.ko      # root-owned copy, checked before loading
NEW_SHA=761608e899ce995218b26393d223aa7d14ea5c32cb15efd8d1a669bb3242f3ec
ORIG=/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko
ORIG_SHA=b62d7dec1c2b91804c909a2c18251488e83b009db88369b2e9fa4573bbc13f67
D=/sys/devices/17000000.gv11b/devfreq/17000000.gv11b
LOG=/home/xnx/gpu-driver-test.log
F="/media/data/gcs-archive/artifacts-bio/swedish-recordings/4k 60 fps 1 960/20 km h/GX011316-001.MP4"
T=/sys/kernel/tracing

say() { echo "$(date '+%H:%M:%S') $*" | tee -a $LOG; sync; }
mhz() { echo $(( $(cat $D/$1 2>/dev/null || echo 0) / 1000000 )); }
start_all() {
    say "starting services again"
    systemctl start nvargus-daemon gdm deepstream deepstream-monitoring gpu-clock-guard
}
holders() { fuser /dev/nvhost-*gpu /dev/nvgpu/igpu0/* 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+' | sort -u; }

[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }

# Stopping gdm runs `loginctl terminate-seat seat0`, which ends EVERY session on the unit's screen and
# keyboard, text consoles included (that killed the first attempt, 11-19 14:07). So the test re-launches
# itself as a transient system service, outside any login session, and you follow the log instead.
if [ -z "$INVOCATION_ID" ]; then
    systemctl reset-failed gpu-driver-test 2>/dev/null
    systemd-run --unit=gpu-driver-test --collect /bin/bash "$(readlink -f "$0")" || { echo "could not start"; exit 1; }
    echo "Test running in the background (unit gpu-driver-test). Your login will be closed when the desktop"
    echo "stops; just log in again here (Ctrl+Alt+F3) and run:   tail -f ~/gpu-driver-test.log"
    sleep 2; exec tail -f $LOG
fi

: > $LOG; chown xnx:xnx $LOG
say "=== GPU driver live test ==="

# 0. preconditions
install -o root -g root -m 0644 "$SRC" $NEW || { say "ABORT: cannot copy $SRC"; exit 1; }
[ "$(sha256sum < $NEW | cut -d' ' -f1)" = "$NEW_SHA" ] || { say "ABORT: $NEW is not the reviewed build"; exit 1; }
[ "$(sha256sum < $ORIG | cut -d' ' -f1)" = "$ORIG_SHA" ] || { say "ABORT: original module not as recorded"; exit 1; }
grep -q '^nvgpu ' /proc/modules || { say "ABORT: nvgpu not loaded"; exit 1; }
say "before: GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz, tpc_pg_mask $(cat /sys/devices/gpu.0/tpc_pg_mask)"

# 1. stop everything that uses the GPU
say "stopping recording, camera daemon, desktop, guard"
systemctl stop gpu-clock-guard deepstream-monitoring deepstream
docker ps --format '{{.Names}}' | grep -qx deepstream_app && docker stop -t 30 deepstream_app > /dev/null
systemctl stop gdm nvargus-daemon
sleep 5
h=$(holders)
if [ -n "$h" ]; then
    say "still using the GPU:"; for p in $h; do say "  $p $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-100)"; done
    say "ABORT: nothing changed; restarting services"; start_all; exit 1
fi
say "nobody uses the GPU (refcount $(awk '$1=="nvgpu"{print $3}' /proc/modules))"

# 2. unload the original
say "unloading the original driver (if this hangs for >2 min: hold the power button; the original comes back)"
if ! timeout 120 rmmod nvgpu; then
    say "rmmod failed; reloading the original"; modprobe nvgpu; start_all; exit 1
fi
say "original unloaded"

# 3. load the fixed one
if ! insmod $NEW; then
    say "FAILED to load the fixed driver: $(dmesg | tail -3 | tr '\n' ' ')"
    say "reloading the original"; modprobe nvgpu && say "original reloaded"; sleep 3
    /usr/sbin/nvpmodel -f /etc/nvpmodel.conf > /dev/null 2>&1; start_all; exit 1
fi
sleep 3
say "fixed driver loaded; kernel messages:"; dmesg | grep -iE 'nvgpu|gv11b' | tail -8 | tee -a $LOG; sync

# 4. power mode, exactly as at boot (sets the 510 MHz cap and the TPC mask before anything uses the GPU)
/usr/sbin/nvpmodel -f /etc/nvpmodel.conf > /dev/null 2>&1
say "after nvpmodel: GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz, tpc_pg_mask $(cat /sys/devices/gpu.0/tpc_pg_mask), mode $(cat /var/lib/nvpmodel/status)"

# 5. everything back
start_all
say "waiting up to 3 min for the recording app to report frames"
ok=0
for i in $(seq 1 36); do
    sleep 5
    perf=$(timeout 10 docker logs --timestamps --tail 50 deepstream_app 2>&1 | grep PERF | tail -1)
    if [ -n "$perf" ]; then
        age=$(( $(date +%s) - $(date -d "${perf%% *}" +%s 2>/dev/null || echo 0) ))
        [ $age -lt 15 ] && { ok=1; break; }
    fi
done
if [ $ok = 1 ]; then say "recording OK: $(echo "$perf" | grep -oE 'FPS_[0-9]+ \([0-9.]+\)' | tr '\n' ' ')"; else say "WARNING: no fresh frame-rate report after 3 min"; fi
say "while recording: GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz"

# 6. the decoder probe that used to stick the clock, with a trace of every GPU clock change
systemctl stop gpu-clock-guard      # so the guard cannot hide a jump during the probe
echo 0 > $T/tracing_on; echo > $T/trace; echo 8192 > $T/buffer_size_kb
echo 'name ~ "*gpc*"' > $T/events/clk/clk_set_rate/filter; echo 1 > $T/events/clk/clk_set_rate/enable
echo 1 > $T/tracing_on
say "probe: hardware decoder on the 4K test video"
sudo -u xnx timeout 30 gst-discoverer-1.0 "$F" > /dev/null 2>&1
sleep 15
echo 0 > $T/tracing_on
rates=$(grep -oE 'clk_set_rate: gpcclk [0-9]+' $T/trace | awk '{print $3/1000000}' | sort -n | uniq -c | tr -s ' ' | tr '\n' ';')
echo 0 > $T/events/clk/clk_set_rate/enable; echo 0 > $T/events/clk/clk_set_rate/filter; echo > $T/trace; echo 1408 > $T/buffer_size_kb
cur=$(mhz cur_freq); cap=$(mhz max_freq)
say "after probe (15 s, guard off): GPU $cur MHz, cap $cap MHz; clock settings seen (count MHz): ${rates:-none}"
systemctl start gpu-clock-guard
if [ "$cur" -le "$cap" ]; then
    say "RESULT: PASS - the clock stayed at or below the cap"
else
    say "RESULT: FAIL - clock above the cap (the guard is back on and will correct it)"
fi
say "The fixed driver stays loaded until the next reboot; a reboot returns to the original."
say "Next: use the desktop (Ctrl+Alt+F1 or F2), open Firefox, play a video; then: journalctl -u gpu-clock-guard --since today"
