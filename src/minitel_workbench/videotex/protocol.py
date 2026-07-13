"""Human-readable annotation of a Videotex byte stream.

The design notebook wished, mid-debugging, that the raw bytes read as intent:
"instead of ``13 41`` show ENVOI; instead of ``1F 48 53`` show *cursor → row 8
col 19*." This module does exactly that. It powers ``minitel inspect`` and the
(roadmapped) live protocol monitor.

It shares the byte vocabulary with the decoder but produces a list of events
rather than drawing a screen.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import constants as C

_COLOURS = C.COLOURS


@dataclass(frozen=True)
class Event:
    offset: int  # byte offset where this event starts
    hex: str  # raw bytes, space-separated hex
    description: str


def _attr_description(code: int) -> str:
    if C.ATTR_FG_BASE <= code <= C.ATTR_FG_BASE + 7:
        return f"foreground {_COLOURS[code - C.ATTR_FG_BASE]}"
    if C.ATTR_BG_BASE <= code <= C.ATTR_BG_BASE + 7:
        return f"background {_COLOURS[code - C.ATTR_BG_BASE]}"
    return {
        C.ATTR_BLINK_ON: "blink on",
        C.ATTR_BLINK_OFF: "blink off",
        C.ATTR_SIZE_NORMAL: "size normal",
        C.ATTR_SIZE_DOUBLE_HEIGHT: "double height",
        C.ATTR_SIZE_DOUBLE_WIDTH: "double width",
        C.ATTR_SIZE_DOUBLE: "double size",
        C.ATTR_CONCEAL_ON: "conceal on",
        C.ATTR_CONCEAL_OFF: "conceal off",
        C.ATTR_UNDERLINE_ON: "underline on",
        C.ATTR_UNDERLINE_OFF: "underline off",
        C.ATTR_INVERSE_ON: "inverse on",
        C.ATTR_INVERSE_OFF: "inverse off",
    }.get(code, f"escape 0x{code:02X}")


def describe_stream(data: bytes) -> list[Event]:
    """Annotate ``data`` as a sequence of Videotex events."""
    events: list[Event] = []
    i = 0
    n = len(data)

    def emit(start: int, end: int, desc: str) -> None:
        events.append(Event(start, data[start:end].hex(" "), desc))

    text_start = -1

    def flush_text(upto: int) -> None:
        nonlocal text_start
        if text_start >= 0:
            run = data[text_start:upto]
            printable = run.decode("latin-1")
            emit(text_start, upto, f"text {printable!r}")
            text_start = -1

    while i < n:
        b = data[i] & 0x7F

        if 0x20 <= b <= 0x7E:
            if text_start < 0:
                text_start = i
            i += 1
            continue

        flush_text(i)

        if b == C.US and i + 2 < n:
            row = (data[i + 1] & 0x7F) - C.POS_OFFSET
            col = (data[i + 2] & 0x7F) - C.POS_OFFSET
            emit(i, i + 3, f"cursor → row {row} col {col}")
            i += 3
            continue
        if b == C.REP and i + 1 < n:
            emit(i, i + 2, f"repeat previous glyph ×{data[i + 1] & 0x3F}")
            i += 2
            continue
        if b == C.ESC and i + 1 < n:
            code = data[i + 1] & 0x7F
            param_len = C.pro_param_len(code)
            if param_len is not None and i + 2 + param_len <= n:
                pro = {C.PRO1: "PRO1", C.PRO2: "PRO2", C.PRO3: "PRO3"}[code]
                emit(i, i + 2 + param_len, f"{pro} protocol sequence")
                i += 2 + param_len
                continue
            emit(i, i + 2, _attr_description(code))
            i += 2
            continue
        if b == C.SS2 and i + 1 < n:
            emit(i, i + 2, f"G2 accent/symbol 0x{data[i + 1] & 0x7F:02X}")
            i += 2
            continue
        if b == C.SEP and i + 1 < n:
            code = data[i + 1] & 0x7F
            try:
                name = C.Key(code).name
            except ValueError:
                name = f"0x{code:02X}"
            emit(i, i + 2, f"KEY {name}")
            i += 2
            continue

        name = C.control_name(b)
        emit(i, i + 1, name or f"byte 0x{b:02X}")
        i += 1

    flush_text(n)
    return events


def format_events(events: list[Event]) -> str:
    """Render events as an aligned, human-readable listing."""
    lines = []
    for ev in events:
        lines.append(f"  {ev.offset:>5}  {ev.hex:<14}  {ev.description}")
    return "\n".join(lines)
