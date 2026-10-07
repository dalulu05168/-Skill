#!/usr/bin/env bash
# Install skill locally into Codex directory. No overwrite, no network activity.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}/romania-stock-intelligence"
test -f "$SRC/SKILL.md" || { echo 'Missing SKILL.md' >&2; exit 1; }
if test -e "$DEST"; then echo "Existing skill not overwritten: $DEST" >&2; exit 1; fi
mkdir -p "$(dirname "$DEST")"
cp -R "$SRC" "$DEST"
echo "Installed at $DEST; reload Codex. No scheduled tasks or market subscriptions created."
