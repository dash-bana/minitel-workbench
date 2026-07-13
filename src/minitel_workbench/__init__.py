"""Minitel Workbench — an open-source toolkit for preserving and extending the
Minitel ecosystem.

The package core imports cleanly with **zero third-party dependencies**. Optional
features (real serial hardware via ``pyserial``; ``ws://``/``wss://`` services via
``websocket-client``; the Tk GUI) are imported lazily at the point of use, so a
telephone-only user — who is the primary audience — is never blocked by a missing
library. See ``CONSTITUTION.md`` (rule II).
"""

__version__ = "0.6.0"

__all__ = ["__version__"]
