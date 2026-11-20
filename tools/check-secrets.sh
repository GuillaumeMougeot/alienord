#!/bin/bash
# Refuses to let credentials into this public repository.
# Runs as the pre-commit and pre-push hook (install: tools/install-hooks.sh) and by hand.
# It reads the live secret values on the unit at run time and never prints them; this file
# itself contains no secret. Usage: tools/check-secrets.sh [--staged]   (default: whole tree)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
ARCHIVE=${VD_PRIVATE_ARCHIVE:-$HOME/vd-biodiversity}     # private repo with Trifork's original docs

# A source that exists must yield its value (an empty value would make grep match everything:
# 2026-11-17), else abort. A source that is absent on this unit (another unit has no private
# repository or bot.env) is listed as not checked. No value at all: abort.
vals=(); missing=()
add(){ if [ ${#2} -lt 6 ]; then echo "check-secrets: ABORT, $1 exists but its value came back empty or too short"; exit 2; fi; vals+=("$2"); }
KEY=/var/secrets/nordfou-biodiversity-2cd0fb3af162.json
if [ -e "$KEY" ]; then add "the cloud key" "$(python3 -c "import json;print(json.load(open('$KEY'))['private_key_id'])" 2>/dev/null)"; else missing+=("cloud key"); fi
if [ -e /var/secrets/bot.env ]; then add "bot.env" "$(grep -oE "ghp_[A-Za-z0-9]+" /var/secrets/bot.env 2>/dev/null | head -1)"; else missing+=("bot.env"); fi
for j in /var/secrets/jfrog_device_token.txt /var/secrets/jfrog_user_token.txt; do      # Trifork's fleet tokens (xnx1)
    [ -e "$j" ] && add "$(basename "$j")" "$(tr -d '[:space:]' < "$j" 2>/dev/null)"
done
if [ -d "$ARCHIVE" ]; then
    f=$(git -C "$ARCHIVE" show HEAD:docs/trifork/flashing_jetson.md 2>/dev/null)
    add "the archive's password 1" "$(echo "$f" | sed -n '32p' | sed -nE 's/.*[Pp]assword\s*[:=]\s*(\S+).*/\1/p')"
    add "the archive's password 2" "$(echo "$f" | sed -n '30p' | sed -nE 's/.*pwd:\s*(\S+).*/\1/p')"
    add "the owner's private address" "$(git -C "$ARCHIVE" config user.email 2>/dev/null)"   # owner's private address
else missing+=("$ARCHIVE (2 passwords, the owner's private address)"); fi
[ ${#vals[@]} -gt 0 ] || { echo "check-secrets: ABORT, no live value could be read on this unit"; exit 2; }
note="${#vals[@]} live values"; [ ${#missing[@]} -gt 0 ] && note="$note; not on this unit, so not checked: $(IFS=,; echo "${missing[*]}")"

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
[ $bad -eq 0 ] && echo "check-secrets: clean ($(echo "$files" | grep -c .) files; $note)"
exit $bad
