#!/bin/bash
# alienord: switch the unit between TEST (indoor) and PRODUCTION (driving) settings, and check readiness.
#
#     bash tools/unit-mode.sh               # status: which mode, and is the unit ready to drive
#     bash tools/unit-mode.sh production    # driving settings, restart the app, then status
#     bash tools/unit-mode.sh test          # indoor settings, restart the app, then status
#
# No sudo needed (the user must be in the docker and apps groups, as xnx is). Recording restarts
# once (~1 min) when the mode changes. Re-running a mode that is already set changes nothing.
#
# The only setting that differs today: camera exposure.
#   test        both cameras may expose up to 100 ms (indoors; too blurred for driving), through the
#               override file /opt/apps/deepstream/config-override/config.yaml mounted into the app
#   production  the image's own values (rear 1 ms, side 0.2 ms): the override is not mounted
# Not touched (decisions, not modes): uploads (off; they would go to Trifork's bucket), the GPU fix.
# Trifork's ENV=test in the compose files is left as is: only ENV=dev changes the app's behaviour.

set -o pipefail
export LC_ALL=C
COMPOSE=/opt/apps/deepstream/docker-compose.yaml
OVERRIDE=/opt/apps/deepstream/config-override/config.yaml
MOUNT="      - $OVERRIDE:/workspaces/vd-biodiversity/bio/configs/config.yaml:ro"
AFTER='      - /media/data/models:/workspaces/vd-biodiversity/bio/models'
APPCFG=/workspaces/vd-biodiversity/bio/configs/config.yaml
D=/sys/devices/17000000.gv11b/devfreq/17000000.gv11b

blockers=(); warnings=()
ok()    { echo "  ok    $*"; }
warn()  { echo "  WARN  $*"; warnings+=("$*"); }
block() { echo "  FIX   $*"; blockers+=("$*"); }

mounted() { grep -qF "$OVERRIDE:/workspaces" "$COMPOSE"; }
exposures() { timeout 20 docker exec deepstream_app sed -n 's/.*AutoExposureTimeMax: *\([0-9]*\).*/\1/p' $APPCFG 2>/dev/null | tr '\n' ' ' | sed 's/ $//'; }

restart_app() {
    local old new i
    old=$(docker inspect -f '{{.Id}}' deepstream_app 2>/dev/null)
    echo "restarting the recording app (applies the change; ~1 min)..."
    docker exec deepstream_app sh -c 'kill -INT $(cat /var/shared/pid/deepstream.pid)' || { echo "could not signal the app"; return 1; }
    for i in $(seq 1 60); do       # new container, then a fresh frame-rate line from it
        sleep 5
        new=$(docker inspect -f '{{.Id}}' deepstream_app 2>/dev/null)
        [ -n "$new" ] && [ "$new" != "$old" ] || continue
        timeout 10 docker logs --tail 20 deepstream_app 2>&1 | grep -q 'PERF' && { echo "app restarted (new container ${new:0:12})"; return 0; }
    done
    echo "the app did not come back with frames within 5 min"; return 1
}

set_mode() {
    local want=$1
    [ -w "$COMPOSE" ] || { echo "cannot write $COMPOSE (need the apps group)"; exit 1; }
    if [ "$want" = production ]; then
        if mounted; then
            cp -p "$COMPOSE" "$COMPOSE.before-unit-mode"
            sed -i "\#$OVERRIDE:/workspaces#d" "$COMPOSE"; sync
            echo "production: exposure override unmounted"; restart_app
        else echo "production: already set"; fi
    else
        grep -q 'AutoExposureTimeMax: 100000' "$OVERRIDE" || { echo "the override file does not hold the indoor values; not changing"; exit 1; }
        if ! mounted; then
            grep -qxF "$AFTER" "$COMPOSE" || { echo "unexpected $COMPOSE layout; not changing"; exit 1; }
            cp -p "$COMPOSE" "$COMPOSE.before-unit-mode"
            sed -i "\#^$AFTER\$#a\\
$MOUNT" "$COMPOSE"; sync
            mounted || { echo "edit failed; restoring"; cp -p "$COMPOSE.before-unit-mode" "$COMPOSE"; exit 1; }
            echo "test: exposure override mounted"; restart_app
        else echo "test: already set"; fi
    fi
}

status() {
    echo; echo "unit $(hostname), $(date '+%F %T'):"
    # mode
    local exp; exp=$(exposures)
    if [ "$exp" = "1000 200" ] && ! mounted; then ok "mode: PRODUCTION (exposure max rear 1 ms, side 0.2 ms)"
    elif [ "$exp" = "100000 100000" ] && mounted; then block "mode: TEST (indoor exposure up to 100 ms: blurred when driving). Run: bash tools/unit-mode.sh production"
    elif [ -z "$exp" ]; then block "mode: unknown (recording app not answering)"
    else block "mode: mixed (running exposure '$exp', override $(mounted && echo mounted || echo not mounted)): restart the app or re-run a mode"; fi
    # services
    local s down=""
    for s in camera deepstream deepstream-monitoring gps gcs; do systemctl is-active -q $s || down="$down $s"; done
    [ -z "$down" ] && ok "services running (camera, deepstream, monitoring, gps, gcs)" || block "services not running:$down"
    # recording: fresh frame-rate line, both cameras > 0
    local perf age n zero
    perf=$(timeout 10 docker logs --timestamps --tail 50 deepstream_app 2>&1 | grep PERF | tail -1)
    if [ -z "$perf" ]; then block "recording: no frame-rate report"
    else
        age=$(( $(date +%s) - $(date -d "${perf%% *}" +%s 2>/dev/null || echo 0) ))
        n=$(grep -oE 'FPS_[0-9]+ \([0-9.]+\)' <<< "$perf" | wc -l)
        zero=$(grep -cE 'FPS_[0-9]+ \(0(\.0+)?\)' <<< "$perf")
        if [ $age -gt 30 ]; then block "recording: last frame-rate report ${age}s old"
        elif [ "$n" -lt 2 ] || [ "$zero" -gt 0 ]; then block "recording: cameras $(grep -oE 'FPS_[0-9]+ \([0-9.]+\)' <<< "$perf" | tr '\n' ' ')(expected 2, both above 0)"
        else ok "recording: $(grep -oE 'FPS_[0-9]+ \([0-9.]+\)' <<< "$perf" | tr '\n' ' ')"; fi
    fi
    # GPS
    local g; g=$(timeout 10 docker logs --tail 40 gps 2>&1 | grep -oE 'Saving new GPS coordinates|NUll Island' | tail -1)
    case "$g" in
        "Saving new GPS coordinates") ok "GPS: fix" ;;
        "NUll Island") warn "GPS: no fix (normal indoors; needs a view of the sky)" ;;
        *) warn "GPS: no recent position messages" ;;
    esac
    # GPU
    local taint mode cur max
    taint=$(cat /sys/module/nvgpu/taint 2>/dev/null); mode=$(cat /var/lib/nvpmodel/status 2>/dev/null)
    cur=$(( $(cat $D/cur_freq 2>/dev/null || echo 0) / 1000000 )); max=$(( $(cat $D/max_freq 2>/dev/null || echo 0) / 1000000 ))
    if [ "$taint" = O ]; then ok "GPU: fixed driver ($mode, ${cur}/${max} MHz)"
    elif systemctl is-active -q gpu-clock-guard; then warn "GPU: original driver; the clock guard covers it ($mode, ${cur}/${max} MHz). Fix: docs/gpu-driver-fix.md"
    else block "GPU: original driver and no clock guard: video or Firefox can overload the supply. Fix: docs/gpu-driver-fix.md"; fi
    [ "$cur" -le "$max" ] || block "GPU clock ${cur} MHz above its cap ${max} MHz"
    [ "$mode" = "pmode:0005" ] || warn "power mode '$mode' (expected pmode:0005)"
    # disk, clock, uploads
    local use; use=$(df --output=pcent /media/data 2>/dev/null | tail -1 | tr -dc 0-9)
    if [ -z "$use" ]; then block "data disk /media/data not mounted"
    elif [ "$use" -ge 90 ]; then block "data disk ${use}% full"
    else ok "data disk ${use}% used ($(df -h --output=avail /media/data | tail -1 | tr -d ' ') free)"; fi
    [ "$(timedatectl show -p NTPSynchronized --value)" = yes ] && ok "clock synchronised" || warn "clock not synchronised (timestamps may drift)"
    if grep -qiE '^UPLOAD_ENABLED=(false|no|off|0)' /opt/apps/gcs/control/upload.conf 2>/dev/null; then
        warn "uploads off: recordings stay on the data disk (pending decision: Trifork's bucket)"
    else ok "uploads on"; fi
    echo
    if [ ${#blockers[@]} = 0 ]; then echo "READY FOR PRODUCTION$([ ${#warnings[@]} -gt 0 ] && echo " (${#warnings[@]} warning(s) above)")"; return 0
    else echo "NOT READY: ${#blockers[@]} thing(s) to fix (FIX lines above)"; return 1; fi
}

case "${1:-status}" in
    status) status ;;
    production|test) set_mode "$1"; status ;;
    *) echo "usage: bash tools/unit-mode.sh [status|production|test]"; exit 2 ;;
esac
