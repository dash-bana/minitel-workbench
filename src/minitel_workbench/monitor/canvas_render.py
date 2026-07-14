"""Turn a Screen into draw operations for a canvas — colour, and real mosaics.

Fonts don't have the Videotex sextant glyphs, so the GUI shouldn't try to *print*
mosaics — it should *draw* them. This produces a flat list of primitive ops
(filled rectangles for backgrounds and the 2x3 mosaic sub-blocks, plus text for
ordinary characters) that a Tk Canvas can execute directly. Keeping it here, as a
pure function, means the drawing logic is testable with no display.
"""

from __future__ import annotations

from .screen import Screen, web_colour

# (x0, y0, x1, y1, fill_hex)
Rect = tuple[str, float, float, float, float, str]
# (cx, cy, char, fill_hex)
Text = tuple[str, float, float, str, str]

# 6-bit mosaic layout: bit -> (col, row) in a 2-wide, 3-tall grid.
_MOSAIC_CELLS = {
    0x01: (0, 0),  # top-left
    0x02: (1, 0),  # top-right
    0x04: (0, 1),  # mid-left
    0x08: (1, 1),  # mid-right
    0x10: (0, 2),  # bottom-left
    0x20: (1, 2),  # bottom-right
}


def cell_draw_ops(
    screen: Screen, cell_w: float, cell_h: float, *, blink_on: bool = True
) -> list[tuple]:
    """Draw ops for the whole screen at the given cell size.

    ``("rect", x0, y0, x1, y1, fill)`` and ``("text", cx, cy, char, fill)``.

    ``blink_on`` is the phase of the blink cycle: on the dark half, cells with
    the blink attribute draw their background only, exactly as the terminal
    shows them. A caller that renders once (a test, a screenshot) can ignore it;
    the live mirror flips it so the Mac blinks when the Minitel does.
    """
    ops: list[tuple] = []
    sub_w = cell_w / 2
    sub_h = cell_h / 3
    for r in range(screen.rows):
        for c in range(screen.cols):
            x0 = c * cell_w
            y0 = r * cell_h
            attr = screen.attr(r, c)
            bg = web_colour(attr.effective_bg)
            # The canvas is already black; only paint non-black backgrounds.
            if bg != "#000000":
                ops.append(("rect", x0, y0, x0 + cell_w, y0 + cell_h, bg))

            if attr.conceal or (attr.blink and not blink_on):
                continue

            fg = web_colour(attr.effective_fg)
            pattern = screen.mosaic_pattern(r, c)
            if pattern is not None:
                for bit, (sc, sr) in _MOSAIC_CELLS.items():
                    if pattern & bit:
                        sx = x0 + sc * sub_w
                        sy = y0 + sr * sub_h
                        ops.append(("rect", sx, sy, sx + sub_w, sy + sub_h, fg))
            else:
                ch = screen.glyph(r, c)
                if ch != " ":
                    ops.append(("text", x0 + cell_w / 2, y0 + cell_h / 2, ch, fg))
    return ops
