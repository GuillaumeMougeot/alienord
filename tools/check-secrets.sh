#!/bin/bash
# Refuses to let credentials into this public repository.
# Runs as the pre-commit and pre-push hook (install: tools/install-hooks.sh) and by hand.
# It reads the live secret values on the unit at run time and never prints them; this file
# itself contains no secret. Usage: tools/check-secrets.sh [--staged]   (default: whole tree)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
ARCHIVE=${VD_PRIVATE_ARCHIVE:-$HOME/vd-biodiversity}     # private repo with Trifork's original docs

vals=()
k=$(python3 -c "import json;print(json.load(open('/var/secrets/nordfou-biodiversity-2cd0fb3af162.json'))['private_key_id'])" 2>/dev/null) && vals+=("$k")
t=$(grep -oE "ghp_[A-Za-z0-9]+" /var/secrets/bot.env 2>/dev/null | head -1) && vals+=("$t")
f=$(git -C "$ARCHIVE" show HEAD:docs/trifork/flashing_jetson.md 2>/dev/null)
p1=$(echo "$f" | sed -n '32p' | sed -nE 's/.*[Pp]assword\s*[:=]\s*(\S+).*/\1/p') && vals+=("$p1")
p2=$(echo "$f" | sed -n '30p' | sed -nE 's/.*pwd:\s*(\S+).*/\1/p') && vals+=("$p2")
e=$(git -C "$ARCHIVE" config user.email 2>/dev/null) && vals+=("$e")   # owner's private address
for v in "${vals[@]}"; do
    if [ ${#v} -lt 6 ]; then echo "check-secrets: ABORT, a live value came back empty or too short (missing /var/secrets or $ARCHIVE?)"; exit 2; fi
done
[ ${#vals[@]} -eq 5 ] || { echo "check-secrets: ABORT, only ${#vals[@]}/5 live values found"; exit 2; }

bad=0
pattern='BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20}|github_pat_|AIza[0-9A-Za-z_-]{30}|tskey-[a-z]+-[A-Za-z0-9]|xox[bp]-[0-9]|"private_key"\s*:'
report(){ while IFS= read -r f; do [ "$f" = tools/check-secrets.sh ] && continue; echo "check-secrets: $1 in $f"; bad=1; done; }
if [ "${1:-}" = "--staged" ]; then
    files=$(git diff --cached --name-only --diff-filter=ACMR)
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        git show ":$f" 2>/dev/null | grep -aqFf <(printf '%s\n' "${vals[@]}") && report "LIVE SECRET VALUE" <<< "$f"
        git show ":$f" 2>/dev/null | grep -aqE -- "$pattern" && report "credential-like pattern" <<< "$f"
    done <<< "$files"
else
    files=$( { git ls-files; git ls-files --others --exclude-standard; } | sort -u)
    report "LIVE SECRET VALUE" < <(echo "$files" | tr '\n' '\0' | xargs -0 grep -alFf <(printf '%s\n' "${vals[@]}") 2>/dev/null)
    report "credential-like pattern" < <(echo "$files" | tr '\n' '\0' | xargs -0 grep -alE -- "$pattern" 2>/dev/null)
fi
[ $bad -eq 0 ] && echo "check-secrets: clean ($(echo "$files" | grep -c .) files)"
exit $bad
