#!/bin/bash
# alienord: bring a stock Trifork unit (as handed over, e.g. xnx1) up to bluemar-bio-xnx-2's fixes.
#
#     sudo bash ~/alienord/tools/stock-unit-fixes.sh
#
# Run it in tmux or over SSH: the model step can take ~10 min. Safe to re-run: each step checks
# whether it is already done. Every replaced file is kept as *.orig-YYYYMMDD. Output is also
# written to /var/log/alienord-stock-unit-fixes.log.
#
#   0. data disk: the unit's data SSD mounted at /media/data at every boot (fstab), with its app
#      folders writable by the apps. On xnx1 it was not: the desktop mounted it at /media/xnx/<uuid>
#      at login, and the apps wrote to a plain folder on the system disk (journal 2026-11-20)
#   1. uploads off: the upload switch + delete-on-failure fix (journal 2026-10-23), only if the gcs
#      image is the one the patched code was written for
#   2. model cache: AI engines saved to /media/data/models, so a restart takes ~30 s instead of
#      ~11 min of yellow LED (journal 2026-09-07). Models copied from THIS unit's image
#   3. LED: yellow also when no frames flow, not only on a stale heartbeat (journal 2026-10-23, 11-16)
#   4. readiness check (tools/unit-mode.sh)
# Steps 0 and 2 restart the recording app (LED yellow meanwhile).
# Reverting: docs/reverting.md (same commands; backups here are *.orig-<today>).

set -o pipefail
export LC_ALL=C
[ "$(id -u)" = 0 ] || { echo "run with sudo: sudo bash $0"; exit 1; }

REPO=$(cd "$(dirname "$0")/.." && pwd)
SRC=$REPO/device/bluemar-bio-xnx-2/opt-apps
DAY=$(date +%Y%m%d)
GCS_IMAGE=aa294dcf3b92          # gcs:base image the patched uploader was taken from
DS=/opt/apps/deepstream/docker-compose.yaml
DEVLINE='      - /opt/apps/deepstream/devices:/opt/apps/deepstream/devices'
MODLINE='      - /media/data/models:/workspaces/vd-biodiversity/bio/models'
LOG=/var/log/alienord-stock-unit-fixes.log
exec > >(tee -a "$LOG") 2>&1
echo "=== $(date '+%F %T') on $(hostname), repo $REPO ($(git -c safe.directory="$REPO" -C "$REPO" rev-parse --short HEAD 2>/dev/null))"

backup() { [ -e "$1.orig-$DAY" ] || cp -p "$1" "$1.orig-$DAY"; }

# restart deepstream the no-root way; done when the app log (UTC) has a "Running..." line written after
# the signal. Not "a new container ID": on xnx1 a restart sometimes recreated the container and
# sometimes restarted the same one (11-20). Not `docker logs --tail 20 | grep PERF`: it missed a
# restart that had worked in 22 s (11-19).
restart_ds() {
    local since
    since=$(date -u '+%F %T')
    docker exec deepstream_app sh -c 'kill -INT $(cat /var/shared/pid/deepstream.pid)' || { echo "could not signal deepstream"; return 1; }
    wait_running "$since" "$1"
}

# wait until the app log (UTC) has a "Running..." line written after $1 (a UTC "%F %T" time)
wait_running() {
    local since=$1 limit=$2 i last
    for i in $(seq 1 $((limit / 5))); do
        sleep 5
        last=$(tail -c 2000000 /var/shared/logs/deepstream.txt | grep -a 'Running\.\.\.' | tail -1 | cut -c1-19)
        [ -n "$last" ] && [[ "$last" > "$since" ]] && { echo "deepstream running after $((i * 5)) s (app log: Running... at $last UTC)"; return 0; }
    done
    echo "deepstream did not log Running... within $limit s"; return 1
}

echo; echo "--- 0. data disk at /media/data"
if mountpoint -q /media/data; then
    echo "already mounted: $(findmnt -n -o SOURCE /media/data)"
else
    # the data SSD: the only ext4 partition over 400 GB that is not on the system disk
    sysdisk=/dev/$(lsblk -no PKNAME "$(findmnt -n -o SOURCE /)")
    cand=()
    while read -r dev fs size type pk; do
        [ "$type" = part ] && [ "$fs" = ext4 ] && [ "$size" -gt 400000000000 ] && [ "/dev/$pk" != "$sysdisk" ] && cand+=("$dev")
    done < <(lsblk -rnbpo PATH,FSTYPE,SIZE,TYPE,PKNAME)
    [ ${#cand[@]} = 1 ] || { echo "expected exactly one data partition, found ${#cand[@]} (${cand[*]}); not changing anything"; exit 1; }
    dev=${cand[0]}; uuid=$(blkid -s UUID -o value "$dev")
    echo "data SSD: $dev, $(lsblk -no SIZE "$dev" | tr -d ' '), UUID $uuid, currently at '$(findmnt -n -o TARGET -S "$dev" | tr '\n' ' ')'"
    echo "stopping the recording app and the uploader..."
    since=$(date -u '+%F %T')
    systemctl stop deepstream-monitoring deepstream gcs
    # stopping the services does not stop deepstream_app (xnx1, 11-20: it ran on, still seeing the old
    # /media/data, and never logged a new "Running..."); stop the containers themselves
    docker stop -t 30 deepstream_app gcs >/dev/null 2>&1
    for m in $(findmnt -n -o TARGET -S "$dev"); do umount "$m" || { echo "cannot unmount $m (a window open on it?); restarting the apps"; systemctl start gcs deepstream deepstream-monitoring; exit 1; }; done
    backup /etc/fstab
    grep -q "$uuid" /etc/fstab || echo "UUID=$uuid /media/data ext4 defaults,nofail,x-systemd.device-timeout=30s 0 2" >> /etc/fstab
    systemctl daemon-reload
    mv /media/data "/media/data.local-$DAY" && mkdir /media/data
    if ! mount /media/data; then
        echo "mount failed; putting everything back"
        rmdir /media/data; mv "/media/data.local-$DAY" /media/data; cp -p /etc/fstab.orig-$DAY /etc/fstab; systemctl daemon-reload
        systemctl start gcs deepstream deepstream-monitoring; exit 1
    fi
    # the apps run as group "shared"; the SSD's own folders and data are otherwise left as they are
    for d in images meta recordings uploaded; do
        mkdir -p /media/data/$d; chgrp shared /media/data/$d; chmod g+rwx /media/data/$d
    done
    [ -d /media/data/models ] || cp -a "/media/data.local-$DAY/models" /media/data/models
    cp -an "/media/data.local-$DAY/recordings/." /media/data/recordings/
    cp -an "/media/data.local-$DAY/images/." /media/data/images/
    cp -an "/media/data.local-$DAY/meta/." /media/data/meta/
    sync
    echo "mounted: $(findmnt -n -o SOURCE,TARGET,OPTIONS /media/data)"
    echo "on the SSD: models $(find /media/data/models -type f | wc -l) files, recordings $(ls /media/data/recordings | wc -l) files; the old folder is kept as /media/data.local-$DAY"
    systemctl start gcs deepstream deepstream-monitoring
    wait_running "$since" 1500
    echo "the app sees: $(docker exec deepstream_app df -h /media/data/recordings | tail -1)"
    docker exec deepstream_app sh -c 't=/media/data/recordings/.write-test; touch $t && rm $t' && echo "the app can write to the SSD" || echo "WARNING: the app cannot write to /media/data/recordings"
fi

echo; echo "--- 1. uploads off"
img=$(docker inspect -f '{{.Image}}' gcs 2>/dev/null | cut -c8-19)
if grep -q 'app-override' /opt/apps/gcs/docker-compose.yaml; then
    echo "already set up"
elif [ "$img" != "$GCS_IMAGE" ]; then
    echo "SKIPPED: gcs image is '$img', the patch was made for $GCS_IMAGE. Stopping the uploader instead."
    systemctl disable --now gcs && echo "gcs service stopped and disabled: nothing is uploaded"
else
    backup /opt/apps/gcs/docker-compose.yaml
    cp -r "$SRC/gcs/app-override" "$SRC/gcs/control" /opt/apps/gcs/
    cp "$SRC/gcs/docker-compose.yaml" /opt/apps/gcs/docker-compose.yaml
    chown -R root:apps /opt/apps/gcs/app-override /opt/apps/gcs/control /opt/apps/gcs/docker-compose.yaml
    chmod -R g+w /opt/apps/gcs/control
    find /opt/apps/gcs/app-override -name __pycache__ -prune -exec rm -r {} +
    sync
    docker stop gcs >/dev/null; echo "gcs restarting with the switch..."
fi
grep -E '^(UPLOAD_ENABLED|DELETE_AFTER_UPLOAD)=' /opt/apps/gcs/control/upload.conf 2>/dev/null
# each cycle logs its mode ("Uploads disabled: ..." appears only when files are waiting)
for i in $(seq 1 12); do
    sleep 5
    m=$(tail -5 /var/shared/logs/gcs.txt | grep -a "Upload mode:" | tail -1)
    [ -n "$m" ] && { echo "gcs log: ${m#* \[INFO\]\[root\]}"; grep -q "UPLOAD_ENABLED=False" <<< "$m" || echo "WARNING: uploads are NOT off"; break; }
    [ $i = 12 ] && { echo "WARNING: no 'Upload mode' line in gcs.txt after 60 s; last lines:"; tail -3 /var/shared/logs/gcs.txt; }
done

echo; echo "--- 2. model cache"
if [ ! -d /media/data/models ]; then
    # copied by the container itself, so the files belong to its user (app:shared) and it can write engines
    docker exec deepstream_app cp -a /workspaces/vd-biodiversity/bio/models /media/data/models || { echo "copy failed; stopping"; exit 1; }
    sync
fi
a=$(docker exec deepstream_app du -sb /workspaces/vd-biodiversity/bio/models 2>/dev/null | cut -f1)
b=$(find /media/data/models -type f ! -name '*.engine' -printf '%s\n' | paste -sd+ | bc)
echo "models: $(find /media/data/models -type f ! -name '*.engine' | wc -l) files, $b bytes (the image's own folder: $a bytes, directories and any saved engines included)"
if grep -qxF "$MODLINE" "$DS"; then
    echo "compose already mounts the model folder"
else
    grep -qxF "$DEVLINE" "$DS" || { echo "unexpected $DS layout; not changing it"; exit 1; }
    backup "$DS"
    sed -i "\\#^$DEVLINE\$#a\\
$MODLINE" "$DS"; sync
    grep -qxF "$MODLINE" "$DS" || { echo "edit failed; restoring"; cp -p "$DS.orig-$DAY" "$DS"; exit 1; }
    echo "compose: model folder mounted. Restart 1 (builds and saves the engines, ~10 min)..."
    restart_ds 1500
    built=1
fi
echo "engines saved: $(find /media/data/models -name '*.engine' | wc -l)"; find /media/data/models -name '*.engine' -printf '  %p %s bytes\n'
if [ "$(find /media/data/models -name '*.engine' | wc -l)" = 0 ]; then
    echo "WARNING: no engines were saved; check: docker logs --tail 400 deepstream_app | grep -i serialize"
elif [ -n "${built:-}" ]; then
    echo "Restart 2 (should load the saved engines, ~30 s)..."
    restart_ds 600
    echo "\"failed to serialize\" lines in the last 400 log lines: $(timeout 10 docker logs --tail 400 deepstream_app 2>&1 | grep -c 'failed to serialize')"
fi

echo; echo "--- 3. LED logic"
M=/opt/apps/deepstream-monitoring
if cmp -s "$M/launch.sh" "$SRC/deepstream-monitoring/launch.sh"; then
    echo "already the new version"
else
    backup "$M/launch.sh"
    cp "$SRC/deepstream-monitoring/launch.sh" "$M/launch.sh"; chown root:apps "$M/launch.sh"; chmod 664 "$M/launch.sh"; sync
    systemctl restart deepstream-monitoring
fi
sleep 35
journalctl -u deepstream-monitoring -n 4 --no-pager

echo; echo "--- 4. readiness"
sudo -u "${SUDO_USER:-xnx}" bash "$REPO/tools/unit-mode.sh" status
echo "=== done $(date '+%F %T'); log: $LOG"
sync
