"""A fully offline Videotex micro-service.

No network, no hardware. It answers keystrokes and draws real Videotex pages
(cursor positioning, text, and a semigraphic box), so the entire chain —
keyboard -> bridge -> service -> bridge -> display/mirror — can be proven on its
own. This is what makes Constitution rule II ("useful with no cable")
demonstrable, and it is the backbone of the end-to-end test.
"""

from __future__ import annotations

import os

from ..channel import ByteChannel, ChannelClosed
from ..videotex import constants as C


def _pos(row: int, col: int) -> bytes:
    """US cursor-position sequence for 1-based row/col."""
    return bytes((C.US, C.POS_OFFSET + row, C.POS_OFFSET + col))


def _mosaic_line(width: int) -> bytes:
    """A run of solid semigraphic blocks (SO … SI)."""
    return bytes([C.SO]) + bytes([0x7F]) * width + bytes([C.SI])


def _home_page() -> bytes:
    out = bytearray()
    out.append(C.FF)  # clear + home
    out += _pos(1, 8)
    out += b"MINITEL WORKBENCH"
    out += _pos(2, 2)
    out += _mosaic_line(36)
    out += _pos(5, 4)
    out += b"1 . INFORMATION"
    out += _pos(7, 4)
    out += b"2 . DEMO SEMIGRAPHIQUE"
    out += _pos(9, 4)
    out += b"3 . A PROPOS"
    out += _pos(11, 4)
    out += b"4 . COULEURS"
    out += _pos(20, 2)
    out += _mosaic_line(36)
    out += _pos(22, 2)
    out += b"CODE + ENVOI : "
    return bytes(out)


def _info_page() -> bytes:
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 10)
    out += b"INFORMATION"
    out += _pos(4, 2)
    out += b"Ceci est un service local de test."
    out += _pos(6, 2)
    out += b"Aucune connexion reseau n'est"
    out += _pos(7, 2)
    out += b"utilisee. Tout fonctionne sans"
    out += _pos(8, 2)
    out += b"cable ni telephone."
    out += _pos(22, 2)
    out += b"SOMMAIRE pour revenir."
    return bytes(out)


def _about_page() -> bytes:
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 12)
    out += b"A PROPOS"
    out += _pos(4, 2)
    out += b"Minitel Workbench"
    out += _pos(6, 2)
    out += b"Toolkit libre pour preserver"
    out += _pos(7, 2)
    out += b"et prolonger le Minitel."
    out += _pos(22, 2)
    out += b"SOMMAIRE pour revenir."
    return bytes(out)


def _demo_page() -> bytes:
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 9)
    out += b"DEMO SEMIGRAPHIQUE"
    for row in range(4, 12):
        out += _pos(row, 6)
        out += _mosaic_line(28)
    out += _pos(22, 2)
    out += b"SOMMAIRE pour revenir."
    return bytes(out)


def _colour_page() -> bytes:
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 12)
    out += b"COULEURS"
    row = 4
    for index, name in enumerate(C.COLOURS):
        if index == 0:
            continue  # black on black is invisible; skip it
        out += _pos(row, 6)
        out += C.set_foreground(index)
        out += name.upper().encode("ascii")
        row += 1
    out += _pos(row + 1, 6)
    out += C.esc(C.ATTR_BLINK_ON) + b"CLIGNOTANT" + C.esc(C.ATTR_BLINK_OFF)
    out += _pos(row + 2, 6)
    out += C.esc(C.ATTR_INVERSE_ON) + b"INVERSE" + C.esc(C.ATTR_INVERSE_OFF)
    out += _pos(22, 2)
    out += b"SOMMAIRE pour revenir."
    return bytes(out)


_PAGES = {
    "1": _info_page,
    "2": _demo_page,
    "3": _about_page,
    "4": _colour_page,
}


class LocalDemoTransport(ByteChannel):
    """In-process Videotex service used for offline testing and demos."""

    def __init__(self, *, name: str = "Local Demo") -> None:
        self.name = name
        self._tx_r, self._tx_w = os.pipe()
        os.set_blocking(self._tx_r, False)
        self._closed = False
        self._input = bytearray()
        self._expect_key = False
        self._send(_home_page())

    # -- outgoing (service -> Minitel) -------------------------------------
    def _send(self, data: bytes) -> None:
        if not self._closed:
            os.write(self._tx_w, data)

    def fileno(self) -> int:
        return self._tx_r

    def read(self, size: int = 4096) -> bytes:
        try:
            data = os.read(self._tx_r, size)
        except BlockingIOError:
            return b""
        if data == b"" and self._closed:
            raise ChannelClosed
        return data

    # -- incoming (Minitel keyboard -> service) ----------------------------
    def write(self, data: bytes) -> None:
        for byte in data:
            if self._expect_key:
                self._expect_key = False
                self._handle_key(byte)
                continue
            if byte == C.SEP:
                self._expect_key = True
                continue
            if 0x20 <= byte <= 0x7E:
                self._input.append(byte)
                self._send(bytes((byte,)))  # echo, since the bridge doesn't

    def _handle_key(self, code: int) -> None:
        if code == C.Key.ENVOI:
            choice = self._input.decode("ascii", "ignore").strip()
            self._input.clear()
            self._go(choice)
        elif code == C.Key.SOMMAIRE:
            self._input.clear()
            self._send(_home_page())
        elif code == C.Key.CORRECTION:
            if self._input:
                self._input.pop()
                self._send(bytes((C.BS, 0x20, C.BS)))
        elif code == C.Key.ANNULATION:
            self._input.clear()

    def _go(self, choice: str) -> None:
        if choice in _PAGES:
            self._send(_PAGES[choice]())
        elif choice in ("", "0"):
            self._send(_home_page())
        else:
            # Unknown code: brief message, then back to the home prompt.
            self._send(_pos(24, 2) + b"CODE INCONNU")
            self._send(_home_page())

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for fd in (self._tx_r, self._tx_w):
            try:
                os.close(fd)
            except OSError:
                pass
