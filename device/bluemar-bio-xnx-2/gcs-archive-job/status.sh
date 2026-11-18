#!/bin/bash
# Progress of the archive job: downloaded vs expected, per bucket.
DEST=/media/data/gcs-archive
systemctl --user is-active gcs-archive >/dev/null && echo "job: running" || echo "job: $(systemctl --user is-active gcs-archive)"
for m in "$DEST"/*.manifest.csv; do
    [ -e "$m" ] || { echo "no manifest yet"; break; }
    b=$(basename "$m" .manifest.csv)
    exp=$(awk -F, '$1 !~ /\/$/ {s+=$2; n++} END {printf "%d %.0f", n, s}' "$m")
    have=$(find "$DEST/$b" -type f ! -name "*_.gstmp" 2>/dev/null | wc -l)
    bytes=$(du -sb "$DEST/$b" 2>/dev/null | cut -f1)
    set -- $exp
    LC_ALL=C awk -v b="$b" -v n="$1" -v s="$2" -v h="$have" -v y="${bytes:-0}" -v done="$([ -f "$DEST/$b.complete" ] && echo ' (complete)')" \
        'BEGIN {printf "%-18s %7d / %7d files   %7.1f / %7.1f GB   %5.1f%%%s\n", b, h, n, y/1e9, s/1e9, (s ? 100*y/s : 0), done}'
done
tail -2 "$DEST"/logs/*.log 2>/dev/null | grep -E "start|complete|retry|failed|verify" | tail -3
