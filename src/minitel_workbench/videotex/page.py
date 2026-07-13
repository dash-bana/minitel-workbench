"""Compose valid Videotex pages from a simple, high-level spec.

Hand-writing cursor/attribute byte sequences is error-prone; this builder lets
code (and, later, the AI generator) describe a page as *content* — a title, some
lines, optional colours — and get correct Videotex bytes back. Keeping the byte
encoding here means the AI only has to produce a small JSON spec, never raw
control codes (which LLMs get wrong).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..monitor.screen import COLS
from . import constants as C


def _colour_index(colour: str | int | None) -> int | None:
    if colour is None:
        return None
    if isinstance(colour, int):
        return colour & 0x07
    name = colour.strip().lower()
    return C.COLOURS.index(name) if name in C.COLOURS else None


@dataclass
class Line:
    text: str
    colour: str | int | None = None
    #: 1-based column; None centres nothing and starts at col 2.
    col: int = 2


@dataclass
class PageSpec:
    title: str = ""
    title_colour: str | int | None = None
    lines: list[Line] = field(default_factory=list)
    footer: str = ""
    #: First body row (1-based). Leaves room for the title + rule.
    body_start: int = 4

    @classmethod
    def from_dict(cls, raw: dict) -> PageSpec:
        lines = []
        for item in raw.get("lines", []):
            if isinstance(item, str):
                lines.append(Line(item))
            else:
                lines.append(
                    Line(
                        item.get("text", ""),
                        item.get("colour", item.get("color")),
                        item.get("col", 2),
                    )
                )
        return cls(
            title=raw.get("title", ""),
            title_colour=raw.get("title_colour", raw.get("title_color")),
            lines=lines,
            footer=raw.get("footer", ""),
            body_start=raw.get("body_start", 4),
        )


def _pos(row: int, col: int) -> bytes:
    return bytes((C.US, C.POS_OFFSET + row, C.POS_OFFSET + col))


def _text(s: str) -> bytes:
    # Videotex G0 is ASCII-ish; drop anything outside it rather than emit junk.
    return s.encode("ascii", "ignore")


def build_page(spec: PageSpec | dict) -> bytes:
    """Return the Videotex bytes for ``spec`` (a ``PageSpec`` or a dict)."""
    if isinstance(spec, dict):
        spec = PageSpec.from_dict(spec)

    out = bytearray()
    out.append(C.FF)  # clear + home

    if spec.title:
        title = spec.title[:COLS]
        col = max(1, (COLS - len(title)) // 2)
        out += _pos(1, col)
        fg = _colour_index(spec.title_colour)
        if fg is not None:
            out += C.set_foreground(fg)
        out += _text(title)
        # a semigraphic rule under the title
        out += _pos(2, 2)
        out += bytes([C.SO]) + bytes([0x7F]) * (COLS - 4) + bytes([C.SI])

    row = spec.body_start
    for line in spec.lines:
        if row > 22:
            break
        out += _pos(row, max(1, line.col))
        fg = _colour_index(line.colour)
        if fg is not None:
            out += C.set_foreground(fg)
        out += _text(line.text)[: COLS - line.col]
        row += 1

    if spec.footer:
        out += _pos(23, 2)
        out += _text(spec.footer)[: COLS - 2]

    return bytes(out)
