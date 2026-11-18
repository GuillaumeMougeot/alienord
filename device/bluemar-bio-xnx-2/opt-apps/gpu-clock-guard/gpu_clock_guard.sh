#!/bin/bash
# GPU clock guard (alienord, 2026-11-18).
# After the hardware video decoder (nvv4l2decoder) is used, or Firefox starts, the GPU clock is
# left at its maximum (1109 MHz) while the frequency governor still believes it runs at the
# power-mode cap (510 MHz). That adds ~8 W; the power supply cuts out 40-70 min later.
# Re-writing the same cap is a no-op; lowering the cap one step for a second and restoring it
# makes the governor really set the clock again.
#
# Normal operation is never touched: the guard only acts while the clock is ABOVE the cap,
# which the governor itself never does. It never changes the power mode, and it always
# restores the cap it found (verified, retried), so nvpmodel / jetson_clocks keep working.
D=/sys/devices/17000000.gv11b/devfreq/17000000.gv11b
INTERVAL=5
strikes=0
while true; do
    cur=$(cat $D/cur_freq); cap=$(cat $D/max_freq)
    if [ "$cur" -gt "$cap" ]; then
        strikes=$((strikes + 1))
        if [ $strikes -ge 2 ]; then
            lower=$(tr ' ' '\n' < $D/available_frequencies | awk -v c="$cap" '$1+0 < c+0' | sort -n | tail -1)
            if [ -n "$lower" ]; then
                echo "GPU clock $((cur/1000000)) MHz above cap $((cap/1000000)) MHz - bouncing cap via $((lower/1000000)) MHz"
                echo "$lower" > $D/max_freq; sleep 1
                for try in 1 2 3; do
                    echo "$cap" > $D/max_freq
                    [ "$(cat $D/max_freq)" = "$cap" ] && break
                    sleep 1
                done
                [ "$(cat $D/max_freq)" = "$cap" ] || echo "WARNING: could not restore cap $((cap/1000000)) MHz (now $(( $(cat $D/max_freq)/1000000 )) MHz)"
                sleep 1
                echo "GPU clock now $(( $(cat $D/cur_freq) / 1000000 )) MHz, cap $(( $(cat $D/max_freq) / 1000000 )) MHz"
            fi
            strikes=0
        fi
    else
        strikes=0
    fi
    sleep $INTERVAL
done
