#!/bin/bash
# Build the site from the last commit under the /UIUX path and sync it to the Singapore mirror.
# Always deploys committed state (git archive), never a co-worker's uncommitted edits.
# The server lives behind the ssh alias "sg-server" (IP only in ~/.ssh/config, never in this repo).
set -euo pipefail
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
BASE=/UIUX
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git archive HEAD | tar -x -C "$TMP"
cd "$TMP"
python3 scripts/validate-data.py
python3 build.py
python3 scripts/prepare-pages.py site --base "$BASE"
python3 scripts/verify-site.py site --base "$BASE"
rsync -az --delete site/ sg-server:/var/www/UIUX/
echo "Singapore mirror updated from commit $REV at $BASE/."
