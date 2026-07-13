#!/bin/bash
# Double-clickable macOS launcher for Minitel Workbench.
# Creates/uses a local virtual environment, then opens the desktop window,
# falling back to the offline demo on the command line if Tk isn't available.
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "First run: setting up a private Python environment…"
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip >/dev/null
  # Serial + WebSocket extras so a real cable and Retrocampus both work.
  ./.venv/bin/python -m pip install -e ".[serial,ws]"
fi

# gui returns non-zero (with a friendly hint) when Tk is missing.
if ! ./.venv/bin/python -m minitel_workbench.gui; then
  echo
  ./.venv/bin/python -m minitel_workbench demo
fi
