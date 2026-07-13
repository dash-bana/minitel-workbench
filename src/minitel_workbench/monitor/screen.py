"""A 24x40 character-cell screen model — the substrate for the Mac mirror.

It is deliberately capability-level-1: it stores glyphs, not colour or DRCS. The
future CEPT renderer will attach attributes to these same cells rather than
replacing the model (Constitution rule VII: never reduce older-terminal support).
"""

from __future__ import annotations

ROWS = 24
COLS = 40


class Screen:
    """Mutable grid of character cells with a single cursor.

    Coordinates are 0-based internally; row 0 is the top content line.
    """

    def __init__(self, rows: int = ROWS, cols: int = COLS) -> None:
        self.rows = rows
        self.cols = cols
        self.row = 0
        self.col = 0
        self._cells: list[list[str]] = [[" "] * cols for _ in range(rows)]

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

    # -- editing ------------------------------------------------------------
    def clear(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                self._cells[r][c] = " "
        self.home()

    def clear_to_end_of_row(self) -> None:
        for c in range(self.col, self.cols):
            self._cells[self.row][c] = " "

    def put(self, ch: str) -> None:
        """Write one glyph at the cursor and advance (wrapping/scrolling)."""
        self._cells[self.row][self.col] = ch
        if self.col < self.cols - 1:
            self.col += 1
        else:
            self.col = 0
            self.cursor_down()

    def _scroll_up(self) -> None:
        self._cells.pop(0)
        self._cells.append([" "] * self.cols)

    # -- output -------------------------------------------------------------
    def line(self, row: int) -> str:
        return "".join(self._cells[row])

    @property
    def text(self) -> str:
        """The whole screen as text, trailing blanks on each line stripped."""
        return "\n".join(self.line(r).rstrip() for r in range(self.rows))

    def framed(self) -> str:
        """The screen inside a box — handy for the CLI mirror / screenshots."""
        top = "┌" + "─" * self.cols + "┐"
        bottom = "└" + "─" * self.cols + "┘"
        body = [f"│{self.line(r)}│" for r in range(self.rows)]
        return "\n".join([top, *body, bottom])
