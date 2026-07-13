#!/bin/bash
# Double-click this to put your Minitel back online.
#
# It finds the project, activates its environment, and connects to your
# last-used service (MiniPavi, Retrocampus, …) with auto-reconnect. No terminal
# knowledge required — just double-click, leave the Minitel at F, and go.
#
# To stop: press Ctrl-C in the window that opens, or just close it.

# Find the project folder whether this launcher sits inside it or on the Desktop.
HERE="$(cd "$(dirname "$0")" && pwd)"
for DIR in "$HERE/.." "$HERE" "$HOME/Downloads/minitel-workbench" "$HOME/minitel-workbench"; do
  if [ -f "$DIR/pyproject.toml" ] && [ -d "$DIR/.venv" ]; then
    PROJECT="$(cd "$DIR" && pwd)"
    break
  fi
done

if [ -z "$PROJECT" ]; then
  echo "Couldn't find the Minitel Workbench folder with its .venv."
  echo "Open it once in Terminal and run the setup from docs/guides/getting-started.md."
  echo "Press any key to close."; read -n 1 -s
  exit 1
fi

cd "$PROJECT"
echo "Minitel Workbench — connecting…"
echo "(Leave the Minitel switched on and showing F. Press Ctrl-C to stop.)"
echo
exec ./.venv/bin/minitel connect
