#!/bin/bash
# Build a standalone "Minitel Workbench.app" (experimental, 1.0 work-in-progress).
#
# The everyday way to launch is the double-clickable
#   scripts/Launch Minitel Workbench.command
# which needs no build step. This script produces a real .app bundle for people
# who want an icon in /Applications, using py2app.
#
# Requires: a working venv with the project installed, plus py2app.
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "Create the environment first (see docs/guides/getting-started.md)."
  exit 1
fi
source .venv/bin/activate
python -m pip install --quiet py2app

# Minimal py2app setup written on the fly so it isn't a permanent project file.
cat > setup_app.py <<'PY'
from setuptools import setup

setup(
    app=["src/minitel_workbench/gui/__main__.py"],
    data_files=[],
    options={"py2app": {
        "argv_emulation": False,
        "packages": ["minitel_workbench"],
        "plist": {"CFBundleName": "Minitel Workbench"},
    }},
    setup_requires=["py2app"],
)
PY

python setup_app.py py2app
rm -f setup_app.py
echo
echo "Built: $(pwd)/dist/  (see the .app inside)"
echo "Note: the desktop GUI is still a skeleton; the CLI is the mature surface."
