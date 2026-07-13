"""A minimal, capability-level-1 Videotex decoder.

It consumes the byte stream a service sends *to* the Minitel and drives a
``Screen`` so the Mac can mirror the display. It handles cursor control, screen
clearing, the text (G0) and semigraphic (G1) sets, and the common G2 accents —
enough to read French service pages. Colour, blink, double-height and DRCS are
intentionally not modelled yet (roadmap 0.7); unknown sequences are skipped
without ever raising.

The decoder is *incremental*: feed it arbitrary chunks and it buffers any partial
multi-byte sequence until the rest arrives.
"""

from __future__ import annotations

import unicodedata

from ..monitor.screen import Screen
from . import constants as C

# G2 diacritics -> Unicode combining marks. Applied to the *next* printable char.
_COMBINING = {
    0x41: "̀",  # grave
    0x42: "́",  # acute
    0x43: "̂",  # circumflex
    0x48: "̈",  # diaeresis (tréma)
    0x4B: "̧",  # cedilla
}

# G2 standalone symbols (best-effort subset).
_G2_SYMBOLS = {
    0x23: "£",
    0x24: "$",
    0x26: "#",
    0x27: "§",
    0x30: "°",
    0x31: "±",
    0x38: "÷",
    0x2C: "←",  # left arrow
    0x2D: "↑",  # up arrow
    0x2E: "→",  # right arrow
    0x2F: "↓",  # down arrow
    0x3C: "¼",
    0x3D: "½",
    0x3E: "¾",
    0x7A: "█",  # solid block (used as a filler in some pages)
}

# Sextant patterns that already have dedicated block glyphs.
_BLOCK_OVERRIDES = {
    0b000000: " ",
    0b111111: "█",  # full block
    0b010101: "▌",  # left half  (top/mid/bottom-left)
    0b101010: "▐",  # right half (top/mid/bottom-right)
}


def _mosaic_glyph(code: int) -> str:
    """Map a Minitel G1 semigraphic byte to a 2x3 Unicode 'sextant' glyph.

    Bit 0x20 selects the graphic rendition (not a pixel); bit 0x40 is the sixth
    pixel. The remaining low five bits are the first five pixels, ordered
    top-left, top-right, mid-left, mid-right, bottom-left.
    """
    pattern = (code & 0x1F) | ((code & 0x40) >> 1)
    if pattern in _BLOCK_OVERRIDES:
        return _BLOCK_OVERRIDES[pattern]
    # Unicode sextants U+1FB00..U+1FB3B are assigned in ascending pattern order,
    # skipping the four patterns above.
    skipped_below = sum(1 for p in _BLOCK_OVERRIDES if p < pattern)
    return chr(0x1FB00 + pattern - 1 - skipped_below)


class Decoder:
    """Stateful Videotex -> Screen interpreter."""

    def __init__(self, screen: Screen | None = None) -> None:
        self.screen = screen if screen is not None else Screen()
        self._buf = bytearray()
        self._graphic = False  # False = G0 text, True = G1 semigraphics
        self._pending_combining: str | None = None

    def feed(self, data: bytes) -> None:
        """Consume bytes, applying every complete token to the screen."""
        self._buf.extend(data)
        i = 0
        n = len(self._buf)
        buf = self._buf

        while i < n:
            b = buf[i] & 0x7F  # 7E1 link: strip any stray parity bit

            # --- sequences that need lookahead ---------------------------
            if b == C.US:
                if i + 2 >= n:
                    break
                row = (buf[i + 1] & 0x7F) - 0x41
                col = (buf[i + 2] & 0x7F) - 0x41
                self.screen.move_to(row, col)
                i += 3
                continue

            if b == C.ESC:
                if i + 1 >= n:
                    break
                self._apply_attribute(buf[i + 1] & 0x7F)
                i += 2
                continue

            if b == C.SS2:
                if i + 1 >= n:
                    break
                code = buf[i + 1] & 0x7F
                if code in _COMBINING:
                    self._pending_combining = _COMBINING[code]
                elif code in _G2_SYMBOLS:
                    self.screen.put(_G2_SYMBOLS[code])
                i += 2
                continue

            if b == C.SEP:
                # Function-key marker (normally Minitel->host); skip SEP + code.
                if i + 1 >= n:
                    break
                i += 2
                continue

            # --- single-byte controls ------------------------------------
            if b == C.SO:
                self._graphic = True
                self.screen.set_pen(mosaic=True)
                i += 1
                continue
            if b == C.SI:
                self._graphic = False
                self.screen.set_pen(mosaic=False)
                i += 1
                continue
            if b == C.FF:
                self.screen.clear()
                self._graphic = False
                i += 1
                continue
            if b == C.RS:
                self.screen.home()
                i += 1
                continue
            if b == C.CR:
                self.screen.carriage_return()
                i += 1
                continue
            if b == C.LF:
                self.screen.cursor_down()
                i += 1
                continue
            if b == C.VT:
                self.screen.cursor_up()
                i += 1
                continue
            if b == C.BS:
                self.screen.cursor_left()
                i += 1
                continue
            if b == C.HT:
                self.screen.cursor_right()
                i += 1
                continue
            if b == C.CAN:
                self.screen.clear_to_end_of_row()
                i += 1
                continue

            # --- printable ------------------------------------------------
            if 0x20 <= b <= 0x7F:
                if self._graphic:
                    self.screen.put(_mosaic_glyph(b))
                else:
                    ch = chr(b)
                    if self._pending_combining:
                        ch = unicodedata.normalize("NFC", ch + self._pending_combining)
                        self._pending_combining = None
                    self.screen.put(ch)
                i += 1
                continue

            # Any other C0 control we don't model: skip it.
            i += 1

        # Keep the unconsumed tail (an incomplete multi-byte sequence).
        del self._buf[:i]

    def _apply_attribute(self, code: int) -> None:
        """Interpret a Teletel attribute (the byte after ESC) onto the pen.

        These are treated as non-spacing here — they change the current pen and
        apply to glyphs written afterwards. Real Minitel colour attributes are
        *serial/spacing* (each occupies a cell); modelling that exactly needs a
        live terminal to validate against and is tracked as a follow-up
        (ROADMAP 0.7). Unknown codes are ignored.
        """
        s = self.screen
        if C.ATTR_FG_BASE <= code <= C.ATTR_FG_BASE + 7:
            s.set_pen(fg=code - C.ATTR_FG_BASE)
        elif C.ATTR_BG_BASE <= code <= C.ATTR_BG_BASE + 7:
            s.set_pen(bg=code - C.ATTR_BG_BASE)
        elif code == C.ATTR_BLINK_ON:
            s.set_pen(blink=True)
        elif code == C.ATTR_BLINK_OFF:
            s.set_pen(blink=False)
        elif code == C.ATTR_SIZE_NORMAL:
            s.set_pen(double_width=False, double_height=False)
        elif code == C.ATTR_SIZE_DOUBLE_HEIGHT:
            s.set_pen(double_height=True)
        elif code == C.ATTR_SIZE_DOUBLE_WIDTH:
            s.set_pen(double_width=True)
        elif code == C.ATTR_SIZE_DOUBLE:
            s.set_pen(double_width=True, double_height=True)
        elif code == C.ATTR_CONCEAL_ON:
            s.set_pen(conceal=True)
        elif code == C.ATTR_CONCEAL_OFF:
            s.set_pen(conceal=False)
        elif code == C.ATTR_UNDERLINE_ON:
            s.set_pen(underline=True)
        elif code == C.ATTR_UNDERLINE_OFF:
            s.set_pen(underline=False)
        elif code == C.ATTR_INVERSE_ON:
            s.set_pen(inverse=True)
        elif code == C.ATTR_INVERSE_OFF:
            s.set_pen(inverse=False)

    @property
    def text(self) -> str:
        return self.screen.text
