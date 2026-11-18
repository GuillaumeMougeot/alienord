#!/bin/bash
# Installs the secret check as this clone's pre-commit and pre-push hooks.
cd "$(git rev-parse --show-toplevel)" || exit 1
printf '#!/bin/sh\nexec tools/check-secrets.sh --staged\n' > .git/hooks/pre-commit
printf '#!/bin/sh\nexec tools/check-secrets.sh\n' > .git/hooks/pre-push
chmod 755 .git/hooks/pre-commit .git/hooks/pre-push tools/check-secrets.sh
echo "hooks installed"
