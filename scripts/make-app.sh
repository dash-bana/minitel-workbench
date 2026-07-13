#!/bin/bash
# Build "Minitel Workbench.app" — a lightweight native bundle that opens the GUI
# window with NO Terminal behind it. It runs the project's existing .venv, so it
# needs no packaging step (py2app etc.) and can't break on a new Python.
#
# Usage: scripts/make-app.sh [output-dir]   (default: ~/Desktop)
set -e
OUT="${1:-$HOME/Desktop}"
APP="$OUT/Minitel Workbench.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Minitel Workbench</string>
  <key>CFBundleDisplayName</key><string>Minitel Workbench</string>
  <key>CFBundleIdentifier</key><string>org.minitel-workbench.app</string>
  <key>CFBundleVersion</key><string>0.6.0</string>
  <key>CFBundleShortVersionString</key><string>0.6.0</string>
  <key>CFBundleExecutable</key><string>minitel-workbench</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSMinimumSystemVersion</key><string>10.13</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/minitel-workbench" <<'RUN'
#!/bin/bash
# Find the project (with its .venv) and open the GUI window.
#
# A double-clicked app has nowhere to print, so a failure to open looks like
# nothing happening at all. Keep the output in a log the user can be pointed at.
LOG="$HOME/minitel-workbench.log"
[ -f "$LOG" ] && [ "$(wc -c <"$LOG")" -gt 1000000 ] && rm -f "$LOG"

for DIR in "$HOME/Downloads/minitel-workbench" "$HOME/minitel-workbench" "$HOME/Desktop/minitel-workbench"; do
  if [ -f "$DIR/pyproject.toml" ] && [ -d "$DIR/.venv" ]; then
    cd "$DIR"
    echo "=== opened $(date)" >>"$LOG"
    exec ./.venv/bin/python -m minitel_workbench.gui >>"$LOG" 2>&1
  fi
done
osascript -e 'display dialog "Could not find the Minitel Workbench project with its .venv. Set it up once (see docs/guides/getting-started.md), then reopen this app." buttons {"OK"} with icon caution'
RUN
chmod +x "$APP/Contents/MacOS/minitel-workbench"

echo "Built: $APP"
