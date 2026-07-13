#!/bin/bash
# Double-click to connect your Minitel directly to Retrocampus.
SERVICE="retrocampus"

HERE="$(cd "$(dirname "$0")" && pwd)"
for DIR in "$HERE/.." "$HERE" "$HOME/Downloads/minitel-workbench" "$HOME/minitel-workbench"; do
  if [ -f "$DIR/pyproject.toml" ] && [ -d "$DIR/.venv" ]; then
    PROJECT="$(cd "$DIR" && pwd)"
    break
  fi
done
if [ -z "$PROJECT" ]; then
  echo "Couldn't find the Minitel Workbench folder with its .venv."
  echo "Press any key to close."; read -n 1 -s
  exit 1
fi

cd "$PROJECT"
echo "Minitel Workbench — connecting to Retrocampus…"
echo "(Leave the Minitel switched on and showing F. Press Ctrl-C to stop.)"
echo
exec ./.venv/bin/minitel connect "$SERVICE"
