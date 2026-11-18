#!/bin/bash
# Mirror the project's Google Cloud buckets onto the SSD, safe to interrupt and rerun.
# For each bucket: write a manifest (name, size, crc32c, md5), rsync, then verify every
# object against the manifest. A bucket counts as done only when verification passes.
# Exits non-zero on any failure, so systemd retries it later; rsync then fetches only
# what is still missing, and gcloud writes each file under a temporary name until it is
# complete, so a cut never leaves a partial file that looks finished.
set -u
DEST=/media/data/gcs-archive
JOB=$(dirname "$(readlink -f "$0")")
mkdir -p "$DEST/logs"

for b in $(grep -vE '^\s*(#|$)' "$JOB/buckets.txt"); do
    log="$DEST/logs/$b.log"
    if [ -f "$DEST/$b.complete" ]; then echo "$b: already complete"; continue; fi
    echo "$(date -Is) $b: start" | tee -a "$log"

    if [ ! -s "$DEST/$b.manifest.csv" ]; then
        gcloud storage objects list "gs://$b/**" \
            --format="csv[no-heading](name,size,crc32c_hash,md5_hash)" > "$DEST/$b.manifest.csv.tmp" 2>>"$log" \
            && mv "$DEST/$b.manifest.csv.tmp" "$DEST/$b.manifest.csv" \
            || { echo "$(date -Is) $b: manifest failed" | tee -a "$log"; exit 1; }
    fi

    # zero-byte "folder" placeholders (names ending in /) carry no data and would clash with directories
    nice -n 10 gcloud storage rsync -r --exclude='.*/$' "gs://$b" "$DEST/$b" >>"$log" 2>&1 \
        || { echo "$(date -Is) $b: rsync interrupted or failed, will retry" | tee -a "$log"; exit 1; }

    python3 "$JOB/verify.py" "$DEST/$b.manifest.csv" "$DEST/$b" 2>&1 | tee -a "$log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "$(date -Is) $b: verification failed, will retry" | tee -a "$log"; exit 1; }
    date -Is > "$DEST/$b.complete"
    echo "$(date -Is) $b: complete" | tee -a "$log"
done
echo "$(date -Is) all buckets complete"
