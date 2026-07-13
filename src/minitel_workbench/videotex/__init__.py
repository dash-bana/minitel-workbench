"""Videotex/Teletel byte-level helpers and a minimal decoder.

Capability level 1 only (monochrome text + semigraphics). Higher levels — colour,
DRCS, double-height — are on the roadmap and will *extend* this, never replace the
L1 fallback (Constitution rule VII).
"""

from .constants import Key, control_name

__all__ = ["Key", "control_name"]
