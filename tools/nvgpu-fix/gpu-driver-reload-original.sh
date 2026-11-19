#!/bin/bash
# Option A (alienord, 2026-11-19): unload and reload the ORIGINAL GPU driver at run time, exactly as
# the live test did with the fixed one, to learn whether reloading by itself crashes the kernel.
#     sudo bash /home/xnx/gpu-test/gpu-driver-reload-original.sh        (from a text console, Ctrl+Alt+F3)
# No new code: the original module from /lib/modules. Nothing written to /lib/modules or the boot config.
# Crash capture: the ramoops module (keeps the kernel's last messages in RAM across a reset) is loaded,
# and kernel.panic=10 makes a crash reset the unit after 10 s (instead of ~4.5 min via the watchdog).
# Both last only until the next boot; kernel.panic is put back at the end if all goes well.
# After a crash and reset:  sudo bash /home/xnx/gpu-test/read-crash-record.sh

ORIG=/lib/modules/5.10.104-tegra/kernel/drivers/gpu/nvgpu/nvgpu.ko
ORIG_SHA=b62d7dec1c2b91804c909a2c18251488e83b009db88369b2e9fa4573bbc13f67
D=/sys/devices/17000000.gv11b/devfreq/17000000.gv11b
LOG=/home/xnx/gpu-test/reload-original.log

say() { echo "$(date '+%H:%M:%S') $*" | tee -a $LOG; sync; }
mhz() { echo $(( $(cat $D/$1 2>/dev/null || echo 0) / 1000000 )); }
start_all() { say "starting services again"; systemctl start nvargus-daemon gdm deepstream deepstream-monitoring gpu-clock-guard; }
holders() { fuser /dev/nvhost-*gpu /dev/nvgpu/igpu0/* 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+' | sort -u; }

[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }

# Stopping gdm logs out every session on the unit's screen and keyboard (gdm runs
# `loginctl terminate-seat seat0`), so the test runs as a background system service.
if [ -z "$INVOCATION_ID" ]; then
    systemctl reset-failed gpu-driver-reload-test 2>/dev/null
    systemd-run --unit=gpu-driver-reload-test --collect /bin/bash "$(readlink -f "$0")" || { echo "could not start"; exit 1; }
    echo "Test running in the background. Your login will be closed when the desktop stops: log in"
    echo "again (Ctrl+Alt+F3) and run:   tail -f ~/gpu-test/reload-original.log"
    echo "If the screen stays black and the keyboard does nothing: wait ~1 min, the unit resets by itself."
    sleep 2; exec tail -f $LOG
fi

: > $LOG; chown xnx:xnx $LOG
say "=== reload the ORIGINAL GPU driver at run time (option A) ==="

# 0. preconditions
[ "$(sha256sum < $ORIG | cut -d' ' -f1)" = "$ORIG_SHA" ] || { say "ABORT: original module not as recorded"; exit 1; }
grep -q '^nvgpu ' /proc/modules || { say "ABORT: nvgpu not loaded"; exit 1; }
[ -z "$(cat /sys/module/nvgpu/taint)" ] || { say "ABORT: the loaded nvgpu is not the original (taint $(cat /sys/module/nvgpu/taint))"; exit 1; }
say "before: GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz, tpc_pg_mask $(cat /sys/devices/gpu.0/tpc_pg_mask)"

# crash capture
modprobe ramoops
OLD_PANIC=$(cat /proc/sys/kernel/panic)
echo 10 > /proc/sys/kernel/panic
say "crash capture: ramoops $(grep -q '^ramoops ' /proc/modules && echo loaded || echo NOT LOADED), panic_on_oops $(cat /proc/sys/kernel/panic_on_oops), reset 10 s after a crash (was $OLD_PANIC)"

# 1. stop everything that uses the GPU
say "stopping recording, camera daemon, desktop, guard"
systemctl stop gpu-clock-guard deepstream-monitoring deepstream
docker ps --format '{{.Names}}' | grep -qx deepstream_app && docker stop -t 30 deepstream_app > /dev/null
systemctl stop gdm nvargus-daemon
sleep 5
h=$(holders)
if [ -n "$h" ]; then
    say "still using the GPU:"; for p in $h; do say "  $p $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-100)"; done
    say "ABORT: nothing changed; restarting services"; echo $OLD_PANIC > /proc/sys/kernel/panic; start_all; exit 1
fi
say "nobody uses the GPU (refcount $(awk '$1=="nvgpu"{print $3}' /proc/modules))"

# 2. unload
if ! timeout 120 rmmod nvgpu; then
    say "rmmod failed; reloading"; modprobe nvgpu; echo $OLD_PANIC > /proc/sys/kernel/panic; start_all; exit 1
fi
say "original unloaded"

# 3. load the same original again
if ! modprobe nvgpu; then
    say "FAILED to reload the original: $(dmesg | tail -3 | tr '\n' ' ')"; say "a reboot brings it back"; exit 1
fi
sleep 3
say "original reloaded (taint '$(cat /sys/module/nvgpu/taint)'); kernel messages:"; dmesg | grep -iE 'nvgpu|gv11b' | tail -6 | tee -a $LOG; sync

# 4. power mode, as at boot
/usr/sbin/nvpmodel -f /etc/nvpmodel.conf > /dev/null 2>&1
say "after nvpmodel: GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz, tpc_pg_mask $(cat /sys/devices/gpu.0/tpc_pg_mask), mode $(cat /var/lib/nvpmodel/status)"

# 5. everything back: the fixed driver crashed 1 s after this point
start_all
for i in 2 5 10 30; do sleep $i; say "alive; desktop X server: $(pgrep -x Xorg > /dev/null && echo running || echo not running)"; done
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
say "GPU $(mhz cur_freq) MHz, cap $(mhz max_freq) MHz; nvgpu errors since reload: $(dmesg | grep -c 'nvgpu.*\[ERR\]')"

echo $OLD_PANIC > /proc/sys/kernel/panic
say "RESULT: NO CRASH - the original driver survives a run-time reload with desktop and recording."
say "So the reload alone does not explain the 14:14 crash: the fixed driver is the suspect."
say "Desktop: Ctrl+Alt+F1. Nothing else to do; tell Claude."
