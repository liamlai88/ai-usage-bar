#!/usr/bin/env bash
# AI Usage Bar — one-shot installer
# Sets up venv, installs deps, and configures the LaunchAgent for auto-start.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "==> Project dir: $PROJECT_DIR"

# 1. venv + deps
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi
echo "==> Installing dependencies..."
"$PROJECT_DIR/.venv/bin/pip" install -q --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"

# 2. LaunchAgent
PLIST_DST="$HOME/Library/LaunchAgents/com.aiusagebar.plist"
echo "==> Installing LaunchAgent at $PLIST_DST"
mkdir -p "$HOME/Library/LaunchAgents"
sed "s|<PROJECT_DIR>|$PROJECT_DIR|g" "$PROJECT_DIR/launchagent.plist.template" > "$PLIST_DST"

# Reload
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load -w "$PLIST_DST"

echo
echo "✅ Done. The widget is running and will start at every login."
echo "   Look at the right side of your menu bar."
echo
echo "Useful commands:"
echo "   Stop:    launchctl unload $PLIST_DST"
echo "   Start:   launchctl load -w $PLIST_DST"
echo "   Logs:    tail -f /tmp/aiusagebar.err.log"
