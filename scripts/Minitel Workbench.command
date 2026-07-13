#!/bin/bash
# Double-click to open the Minitel Workbench window (the front-end).
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
exec ./.venv/bin/python -m minitel_workbench.gui
