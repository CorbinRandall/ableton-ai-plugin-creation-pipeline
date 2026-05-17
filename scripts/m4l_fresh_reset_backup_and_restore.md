# Fresh reset backup / restore

The reset script moves (not deletes) Ableton + Cursor pipeline pieces into a timestamped folder under `~/Music/Ableton/`.

## After a reset — hand restore

1. **Cursor MCP** — copy `mcp.json.bak` over `~/.cursor/mcp.json`, then **restart Cursor**.
2. **Ableton remote script** — move `RemoteScripts/AbletonOSC` (and `AbletonMCP` if present) back into  
   `~/Music/Ableton/User Library/Remote Scripts/`.
3. **Imported device** — copy `Imported/Pipeline_Example.amxd` back to  
   `~/Music/Ableton/User Library/Presets/MIDI Effects/Max MIDI Effect/Imported/` if you want the old file.
4. **Repo venv / builds** — not fully backed up (too large); run `./bootstrap.sh` again, or restore `projects/` version folders from backup if you copied them.

## One-liner restore (adjust `BACKUP` path)

```bash
BACKUP="$HOME/Music/Ableton/m4l_fresh_reset_backup_<YOUR_TIMESTAMP>"
cp "$BACKUP/mcp.json.bak" ~/.cursor/mcp.json
mkdir -p "$HOME/Music/Ableton/User Library/Remote Scripts"
if [ -d "$BACKUP/RemoteScripts/AbletonOSC" ]; then
  mv "$BACKUP/RemoteScripts/AbletonOSC" "$HOME/Music/Ableton/User Library/Remote Scripts/"
fi
if [ -d "$BACKUP/RemoteScripts/AbletonMCP" ]; then
  mv "$BACKUP/RemoteScripts/AbletonMCP" "$HOME/Music/Ableton/User Library/Remote Scripts/"
fi
```

Then restart **Cursor** and **Ableton Live**, and re-select Control Surfaces if needed.
