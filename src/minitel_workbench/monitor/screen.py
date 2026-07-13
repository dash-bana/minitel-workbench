"""A 24x40 character-cell screen model — the substrate for the Mac mirror.

Each cell now carries a CEPT attribute (colour, blink, inverse, underline,
conceal, size, mosaic) alongside its glyph. This is strictly additive: the glyph
side is unchanged, so an older Minitel that only produces monochrome text renders
exactly as before (Constitution rule VII). Renderers can consume the attributes
(ANSI for the terminal, HTML for screenshots) or ignore them.
"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass, replace

from ..videotex.constants import COLOURS

ROWS = 24
COLS = 40


@dataclass(frozen=True)
class Attr:
    """A cell's rendition. Colours are indices 0..7 (ANSI order)."""

    fg: int = 7  # white
    bg: int = 0  # black
    blink: bool = False
    inverse: bool = False
    underline: bool = False
    conceal: bool = False
    double_width: bool = False
    double_height: bool = False
    mosaic: bool = False  # this cell came from the G1 semigraphic set

    @property
    def effective_fg(self) -> int:
        return self.bg if self.inverse else self.fg

    @property
    def effective_bg(self) -> int:
        return self.fg if self.inverse else self.bg


DEFAULT_ATTR = Attr()


class Screen:
    """Mutable grid of (glyph, attribute) cells with a single cursor and pen."""

    def __init__(self, rows: int = ROWS, cols: int = COLS) -> None:
        self.rows = rows
        self.cols = cols
        self.row = 0
        self.col = 0
        self.pen = DEFAULT_ATTR  # current rendition applied to written glyphs
        self._cells: list[list[str]] = [[" "] * cols for _ in range(rows)]
        self._attrs: list[list[Attr]] = [[DEFAULT_ATTR] * cols for _ in range(rows)]
        # Per-cell 6-bit mosaic pattern (or None for text cells). Kept so a
        # graphical renderer can *draw* the 2x3 sub-blocks instead of relying on
        # a font having the Unicode sextant glyphs (most don't).
        self._mosaic: list[list[int | None]] = [[None] * cols for _ in range(rows)]

    # -- cursor -------------------------------------------------------------
    def home(self) -> None:
        self.row = 0
        self.col = 0

    def move_to(self, row: int, col: int) -> None:
        self.row = max(0, min(self.rows - 1, row))
        self.col = max(0, min(self.cols - 1, col))

    def cursor_left(self) -> None:
        self.col = max(0, self.col - 1)

    def cursor_right(self) -> None:
        if self.col < self.cols - 1:
            self.col += 1

    def cursor_up(self) -> None:
        self.row = max(0, self.row - 1)

    def cursor_down(self) -> None:
        if self.row < self.rows - 1:
            self.row += 1
        else:
            self._scroll_up()

    def carriage_return(self) -> None:
        self.col = 0

    # -- pen (rendition) ----------------------------------------------------
    def set_pen(self, **changes: object) -> None:
        self.pen = replace(self.pen, **changes)  # type: ignore[arg-type]

    def reset_pen(self) -> None:
        self.pen = DEFAULT_ATTR

    # -- editing ------------------------------------------------------------
    def clear(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                self._cells[r][c] = " "
                self._attrs[r][c] = DEFAULT_ATTR
                self._mosaic[r][c] = None
        self.reset_pen()
        self.home()

    def clear_to_end_of_row(self) -> None:
        for c in range(self.col, self.cols):
            self._cells[self.row][c] = " "
            self._attrs[self.row][c] = self.pen
            self._mosaic[self.row][c] = None

    def put(self, ch: str, mosaic: int | None = None) -> None:
        """Write one glyph with the current pen and advance (wrap/scroll).

        ``mosaic`` is the 6-bit semigraphic pattern when the glyph is a mosaic
        cell, or ``None`` for ordinary text.
        """
        self._cells[self.row][self.col] = ch
        self._attrs[self.row][self.col] = self.pen
        self._mosaic[self.row][self.col] = mosaic
        if self.col < self.cols - 1:
            self.col += 1
        else:
            self.col = 0
            self.cursor_down()

    def _scroll_up(self) -> None:
        self._cells.pop(0)
        self._cells.append([" "] * self.cols)
        self._attrs.pop(0)
        self._attrs.append([DEFAULT_ATTR] * self.cols)
        self._mosaic.pop(0)
        self._mosaic.append([None] * self.cols)

    def mosaic_pattern(self, row: int, col: int) -> int | None:
        """The 6-bit semigraphic pattern at a cell, or None if it's text."""
        return self._mosaic[row][col]

    # -- access -------------------------------------------------------------
    def glyph(self, row: int, col: int) -> str:
        return self._cells[row][col]

    def attr(self, row: int, col: int) -> Attr:
        return self._attrs[row][col]

    def line(self, row: int) -> str:
        return "".join(self._cells[row])

    @property
    def text(self) -> str:
        """The whole screen as text, trailing blanks on each line stripped."""
        return "\n".join(self.line(r).rstrip() for r in range(self.rows))

    def framed(self, color: bool = False) -> str:
        """The screen inside a box. With ``color=True``, cells are ANSI-coloured."""
        top = "┌" + "─" * self.cols + "┐"
        bottom = "└" + "─" * self.cols + "┘"
        if not color:
            body = [f"│{self.line(r)}│" for r in range(self.rows)]
        else:
            body = [f"│{self._ansi_row(r)}│" for r in range(self.rows)]
        return "\n".join([top, *body, bottom])

    # -- ANSI rendering (terminal mirror) ----------------------------------
    def _ansi_row(self, row: int) -> str:
        out = []
        last: Attr | None = None
        for col in range(self.cols):
            a = self._attrs[row][col]
            if a != last:
                out.append(_ansi_sgr(a))
                last = a
            ch = " " if a.conceal else self._cells[row][col]
            out.append(ch)
        out.append("\x1b[0m")
        return "".join(out)

    def to_ansi(self) -> str:
        return "\n".join(self._ansi_row(r) + "\x1b[0m" for r in range(self.rows))

    # -- HTML rendering (screenshots / docs, dependency-free) --------------
    def to_html(self, *, title: str = "Minitel screen") -> str:
        cells = []
        for r in range(self.rows):
            row_html = []
            for c in range(self.cols):
                a = self._attrs[r][c]
                ch = " " if a.conceal else self._cells[r][c]
                fg = _WEB_COLOURS[a.effective_fg]
                bg = _WEB_COLOURS[a.effective_bg]
                style = [f"color:{fg}", f"background:{bg}"]
                if a.underline:
                    style.append("text-decoration:underline")
                if a.blink:
                    style.append("animation:mtl-blink 1s steps(1) infinite")
                row_html.append(f'<span style="{";".join(style)}">{_html.escape(ch)}</span>')
            cells.append("".join(row_html))
        grid = "\n".join(cells)
        return (
            f"<!doctype html><meta charset=utf-8><title>{_html.escape(title)}</title>"
            "<style>@keyframes mtl-blink{50%{opacity:0}}"
            "pre.mtl{display:inline-block;padding:12px;background:#000;"
            "font:14px/1.15 'Menlo','DejaVu Sans Mono',monospace;letter-spacing:0}"
            "</style>"
            f'<pre class="mtl">{grid}</pre>'
        )


# ANSI colour indices already match COLOURS order (0 black .. 7 white).
_WEB_COLOURS = (
    "#000000",  # black
    "#ff5555",  # red
    "#55ff55",  # green
    "#ffff55",  # yellow
    "#5555ff",  # blue
    "#ff55ff",  # magenta
    "#55ffff",  # cyan
    "#e0e0e0",  # white
)

assert len(_WEB_COLOURS) == len(COLOURS)


def web_colour(index: int) -> str:
    """Hex colour for a Minitel colour index (0..7)."""
    return _WEB_COLOURS[index & 0x07]


def _ansi_sgr(a: Attr) -> str:
    codes = ["0", str(30 + a.effective_fg), str(40 + a.effective_bg)]
    if a.blink:
        codes.append("5")
    if a.underline:
        codes.append("4")
    return "\x1b[" + ";".join(codes) + "m"
