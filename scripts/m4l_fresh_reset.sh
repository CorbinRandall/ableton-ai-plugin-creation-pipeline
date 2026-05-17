#!/usr/bin/env bash
# Reset M4L public-pipeline artifacts to approximate a "just cloned repo" state.
# Backs up (moves/copies) Ableton Remote Scripts, Cursor MCP config, and tutorial imports.
#
# IMPORTANT: Quit Ableton Live completely before running (otherwise scripts may be locked).
#
# Usage (from repo root):
#   bash scripts/m4l_fresh_reset.sh
#
# Restore: see scripts/m4l_fresh_reset_backup_and_restore.md inside the backup folder.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${HOME}/Music/Ableton/m4l_fresh_reset_backup_${STAMP}"
ABLETON_HOME="${ABLETON_HOME:-$HOME/Music/Ableton}"
RS_DEST="$ABLETON_HOME/User Library/Remote Scripts"
IMPORTED="$ABLETON_HOME/User Library/Presets/MIDI Effects/Max MIDI Effect/Imported"
MCP_JSON="${HOME}/.cursor/mcp.json"

mkdir -p "$BACKUP/RemoteScripts"
cp "$ROOT/scripts/m4l_fresh_reset_backup_and_restore.md" "$BACKUP/RESTORE.md"

echo "Backup root: $BACKUP"
echo "Ableton home: $ABLETON_HOME"
echo ""

if [ -f "$MCP_JSON" ]; then
  cp "$MCP_JSON" "$BACKUP/mcp.json.bak"
  printf '%s\n' '{"mcpServers": {}}' > "$MCP_JSON"
  echo "✓ Cursor: backed up ~/.cursor/mcp.json → backup; replaced with empty mcpServers (restart Cursor)."
else
  echo "WARN: No $MCP_JSON (skip MCP reset)."
fi

for name in AbletonOSC AbletonMCP; do
  src="$RS_DEST/$name"
  if [ -d "$src" ]; then
    mv "$src" "$BACKUP/RemoteScripts/$name"
    echo "✓ Moved Remote Script $name → backup (removed from Live User Library)."
  fi
done

if [ -f "$IMPORTED/Pipeline_Example.amxd" ]; then
  mkdir -p "$BACKUP/Imported"
  mv "$IMPORTED/Pipeline_Example.amxd" "$BACKUP/Imported/"
  echo "✓ Moved Imported/Pipeline_Example.amxd → backup."
fi

# Repo-local clean (like fresh clone + no local venv)
if [ -d "$ROOT/venv" ]; then
  rm -rf "$ROOT/venv"
  echo "✓ Removed $ROOT/venv"
fi
if [ -d "$ROOT/.bootstrap_cache" ]; then
  rm -rf "$ROOT/.bootstrap_cache"
  echo "✓ Removed $ROOT/.bootstrap_cache"
fi
shopt -s nullglob
for d in "$ROOT/projects/Pipeline_Example"/Pipeline_Example\ *.*; do
  if [ -d "$d" ]; then
    rm -rf "$d"
    echo "✓ Removed version folder $d"
  fi
done
shopt -u nullglob

echo ""
echo "Done. Next:"
echo "  1) Restart Cursor (MCP config changed)."
echo "  2) From repo root:  chmod +x bootstrap.sh && ./bootstrap.sh"
echo "  3) Open Live → Preferences → Link/Tempo/MIDI → AbletonOSC + AbletonMCP"
echo "  4) ./venv/bin/python scripts/verify_setup.py --wait-mcp 120"
echo ""
echo "Recover old setup from: $BACKUP (see RESTORE.md there)."
