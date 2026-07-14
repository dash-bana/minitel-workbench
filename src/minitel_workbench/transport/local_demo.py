"""A fully offline Videotex micro-service.

No network, no hardware. It answers keystrokes and draws real Videotex pages
(cursor positioning, text, and a semigraphic box), so the entire chain —
keyboard -> bridge -> service -> bridge -> display/mirror — can be proven on its
own. This is what makes Constitution rule II ("useful with no cable")
demonstrable, and it is the backbone of the end-to-end test.
"""

from __future__ import annotations

import os
import unicodedata

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
    # Say what this is on the page itself: a user looking at the terminal has no
    # README in front of them.
    out += _pos(4, 2)
    out += fr("Service local. Aucun réseau utilisé.")
    out += _pos(5, 2)
    out += fr("Si ces pages sont correctes, votre")
    out += _pos(6, 2)
    out += fr("Minitel et votre câble sont bons.")
    out += _pos(9, 4)
    out += b"1 . POURQUOI CE SERVICE ?"
    out += _pos(11, 4)
    out += b"2 . DEMO SEMIGRAPHIQUE"
    out += _pos(13, 4)
    out += b"3 . A PROPOS"
    out += _pos(15, 4)
    out += b"4 . COULEURS"
    out += _pos(17, 4)
    out += b"5 . TEST AFFICHAGE"
    out += _pos(20, 2)
    out += _mosaic_line(36)
    out += _pos(22, 2)
    out += b"CODE + ENVOI : "
    return bytes(out)


def _info_page() -> bytes:
    """Why this service exists — the bisection argument, on the terminal itself.

    Someone who clicks "Local Demo" and sees a menu is entitled to ask what it is
    for. Answering only in the documentation answers nobody: they are looking at
    a Minitel, not a README.
    """
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 6)
    out += b"POURQUOI CE SERVICE ?"
    out += _pos(3, 2)
    out += fr("Ces pages viennent de Workbench")
    out += _pos(4, 2)
    out += fr("lui-même : ni réseau, ni serveur,")
    out += _pos(5, 2)
    out += fr("ni téléphone.")
    out += _pos(7, 2)
    out += fr("Si ces pages se chargent")
    out += _pos(8, 2)
    out += fr("correctement, tout va bien de votre")
    out += _pos(9, 2)
    out += fr("côté ; tout problème survenant en")
    out += _pos(10, 2)
    out += fr("fonctionnement normal a une autre")
    out += _pos(11, 2)
    out += fr("origine.")
    out += _pos(13, 2)
    out += fr("Si elles sont fausses, la panne est")
    out += _pos(14, 2)
    out += fr("ici. La page 5 vous dira où.")
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
    out += fr("Toolkit libre pour préserver")
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


def _accent(code: int, letter: bytes) -> bytes:
    """A G2 diacritic applied to the next letter (SS2 <code> <letter>)."""
    return bytes((C.SS2, code)) + letter


#: Accented letters -> their G2 diacritic code. Videotex has no accented glyphs:
#: the accent is a shift (SS2) applied to the *following* plain letter.
_DIACRITICS = {
    "̀": 0x41,  # grave
    "́": 0x42,  # acute
    "̂": 0x43,  # circumflex
    "̈": 0x48,  # diaeresis
    "̧": 0x4B,  # cedilla
}


def fr(text: str) -> bytes:
    """Encode French text for the terminal, accents and all.

    Written as ordinary French ("côté", "problème") and encoded here, rather than
    spelled out at every call site — and rather than dropping the accents, which
    is what the demo used to do and which reads as bad French, not as a choice.
    """
    out = bytearray()
    for ch in unicodedata.normalize("NFD", text):
        code = _DIACRITICS.get(ch)
        if code is None:
            out += ch.encode("ascii", "replace")
            continue
        # A combining mark follows its letter in Unicode, but *precedes* it in
        # Videotex — so take the letter back off and re-emit it after the shift.
        letter = bytes(out[-1:])
        del out[-1:]
        out += _accent(code, letter)
    return bytes(out)


def _test_card() -> bytes:
    """A test card, in the television sense: a page whose correct appearance is
    known and *stated on the page itself*.

    Every line exercises one thing that really breaks in this chain — accents
    (which come out wrong when the framing is not 7E1), the mosaic set, REP
    run-length fills, the 40-column boundary, and the display attributes — and
    says what it must look like. That way a garbled screen is diagnostic rather
    than merely disappointing: the user can say *which* line is wrong, and a
    photograph of it is enough to work from.
    """
    out = bytearray()
    out.append(C.FF)
    out += _pos(1, 11)
    out += b"TEST AFFICHAGE"

    # 1. Accents (G2). Wrong framing mangles these first.
    #
    # The specimens are accented; the "attendu" lines that describe them are
    # deliberately plain ASCII, and must stay that way. They are read precisely
    # when accents are broken — a caption that fails with the thing it describes
    # is no use to anyone.
    out += _pos(3, 2)
    out += b"ACCENTS    "
    out += _accent(0x42, b"E") + _accent(0x41, b"E") + _accent(0x41, b"A")
    out += _accent(0x4B, b"C") + _accent(0x43, b"O") + _accent(0x48, b"I")
    out += _pos(4, 2)
    out += b"  attendu: E aigu, E grave, A grave,"
    out += _pos(5, 2)
    out += b"           C cedille, O circonflexe,"
    out += _pos(6, 2)
    out += b"           I trema"

    # 2. Semigraphics: a solid bar, no gaps.
    out += _pos(8, 2)
    out += b"MOSAIQUE   "
    out += _mosaic_line(20)
    out += _pos(9, 2)
    out += b"  attendu: barre pleine, sans trous"

    # 3. REP run-length fill: one glyph, then a repeat count.
    out += _pos(11, 2)
    out += b"REPETITION "
    out += b"-" + bytes((C.REP, C.POS_OFFSET + 19))  # the '-' plus 19 more = 20
    out += _pos(12, 2)
    out += b"  attendu: 20 tirets identiques"

    # 4. The 40-column boundary: the bar must touch both edges, and not wrap.
    out += _pos(14, 1)
    out += b"|" + b"-" * 38 + b"|"
    out += _pos(15, 2)
    out += b"  attendu: barres aux colonnes 1 et 40"

    # 5. Display attributes. On a monochrome set these are grey levels, which is
    #    correct — hence "clair", not a colour name.
    out += _pos(17, 2)
    out += b"INVERSE    "
    out += C.esc(C.ATTR_INVERSE_ON) + b"INVERSE" + C.esc(C.ATTR_INVERSE_OFF)
    out += _pos(18, 2)
    out += b"CLIGNOTANT "
    out += C.esc(C.ATTR_BLINK_ON) + b"CLIGNOTE" + C.esc(C.ATTR_BLINK_OFF)

    out += _pos(20, 2)
    out += b"Tout correct: la chaine est bonne."
    out += _pos(21, 2)
    out += b"Sinon, notez la ligne fautive."
    out += _pos(22, 2)
    out += b"SOMMAIRE pour revenir."
    return bytes(out)


_PAGES = {
    "1": _info_page,
    "2": _demo_page,
    "3": _about_page,
    "4": _colour_page,
    "5": _test_card,
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
