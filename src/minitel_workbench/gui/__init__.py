"""Optional Tk desktop shell.

The GUI is never required: if Tk is missing (as on stock Homebrew Python 3.14,
per the design notebook), :func:`run` returns a precise, actionable install hint
instead of raising — and the CLI remains fully functional.
"""

from __future__ import annotations


def run() -> int:
    try:
        import tkinter  # noqa: F401
    except Exception:
        print(
            "The desktop window needs Tk, which your Python was built without.\n"
            "On macOS with Homebrew:  brew install python-tk\n"
            "Meanwhile, everything works from the command line — try:  minitel demo"
        )
        return 1

    from .app import WorkbenchApp

    WorkbenchApp().run()
    return 0
