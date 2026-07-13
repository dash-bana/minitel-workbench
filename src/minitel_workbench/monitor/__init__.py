"""The Mac-side mirror: a model of what the Minitel is displaying.

Today this renders capability level 1 (monochrome text + semigraphics) to plain
text / Unicode blocks. A full CEPT colour/mosaic/DRCS renderer is the headline
roadmap item and will build on the same ``Screen`` model.
"""

from .screen import COLS, ROWS, Screen

__all__ = ["Screen", "ROWS", "COLS"]
