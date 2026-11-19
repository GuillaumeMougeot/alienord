#!/bin/bash
# compare_ko.sh <reference.ko> <candidate.ko>
R=$1; C=$2; T=$(mktemp -d)
for x in R C; do f=${!x}
  modinfo -F vermagic $f > $T/$x.vermagic; modinfo $f | grep -vE '^filename' | sort > $T/$x.modinfo
  python3 -I /home/xnx/build/nvgpu-fix/tools/versions.py $f | sort > $T/$x.versions
  nm $f | awk '$2 ~ /^[TtDdBbRr]$/ {print $3}' | grep -vE '^(\.L|__UNIQUE_ID|__func__|__compound_literal|CSWTCH)' | sed 's/\.[0-9]*$//;s/\.constprop.*//;s/\.isra.*//;s/\.part.*//' | sort -u > $T/$x.syms
  nm $f | awk '$3 ~ /^__ksymtab_/ {print $3}' | sort > $T/$x.exports
  strings -n 6 $f | grep -v '/home/' | sort -u > $T/$x.strings
done
echo "vermagic: $(cat $T/R.vermagic) | $(cat $T/C.vermagic)"
echo "modinfo diff:"; diff $T/R.modinfo $T/C.modinfo | grep '^[<>]' | grep -vE 'srcversion|^[<>] (alias|parm|depends|intree|name|vermagic|retpoline):' | head
echo "imports: ref $(wc -l < $T/R.versions), cand $(wc -l < $T/C.versions), differing lines $(diff $T/R.versions $T/C.versions | grep -c '^[<>]')"; diff $T/R.versions $T/C.versions | grep '^[<>]' | head -10
echo "exports: ref $(wc -l < $T/R.exports), cand $(wc -l < $T/C.exports), differing $(diff $T/R.exports $T/C.exports | grep -c '^[<>]')"
echo "symbols: ref $(wc -l < $T/R.syms), cand $(wc -l < $T/C.syms), only-ref $(comm -23 $T/R.syms $T/C.syms | wc -l), only-cand $(comm -13 $T/R.syms $T/C.syms | wc -l)"; echo " only-ref e.g.: $(comm -23 $T/R.syms $T/C.syms | head -8 | tr '\n' ' ')"; echo " only-cand e.g.: $(comm -13 $T/R.syms $T/C.syms | head -8 | tr '\n' ' ')"
echo "strings: ref $(wc -l < $T/R.strings), cand $(wc -l < $T/C.strings), only-ref $(comm -23 $T/R.strings $T/C.strings | wc -l), only-cand $(comm -13 $T/R.strings $T/C.strings | wc -l)"; echo " only-ref e.g.:"; comm -23 $T/R.strings $T/C.strings | head -8; echo " only-cand e.g.:"; comm -13 $T/R.strings $T/C.strings | head -8
size $R $C
rm -r $T
