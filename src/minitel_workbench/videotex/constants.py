"""Named Videotex/Teletel byte constants.

These are the codes used by Minitel terminals on the peripheral (DIN) link. They
let the protocol monitor and decoder speak in human terms ("ENVOI", "cursor to
row 8 col 19") instead of raw hex — exactly the readability the design notebook
asked for.
"""

from __future__ import annotations

from enum import IntEnum

# --- C0 control characters -------------------------------------------------
NUL = 0x00
BEL = 0x07
BS = 0x08  # cursor left
HT = 0x09  # cursor right
LF = 0x0A  # cursor down
VT = 0x0B  # cursor up
FF = 0x0C  # clear screen + cursor home
CR = 0x0D  # cursor to column 1 of current row
SO = 0x0E  # shift out -> G1 (semigraphic / mosaic set)
SI = 0x0F  # shift in  -> G0 (text set)
CAN = 0x18  # fill to end of row with spaces
SUB = 0x1A
ESC = 0x1B  # introduces C1 / attribute sequences
SS2 = 0x19  # single shift 2 -> next char from G2 (accents, symbols)
RS = 0x1E  # cursor home (row 1, col 1)
US = 0x1F  # cursor positioning: US <0x40+row> <0x40+col>
SEP = 0x13  # separator: introduces a Minitel function-key code

# Offset added to row/column numbers in a US positioning sequence.
POS_OFFSET = 0x40


class Key(IntEnum):
    """Minitel function keys, as the second byte following ``SEP`` (0x13).

    Example from the notebook: pressing ENVOI transmits ``13 41``.
    """

    ENVOI = 0x41
    RETOUR = 0x42
    REPETITION = 0x43
    GUIDE = 0x44
    ANNULATION = 0x45
    SOMMAIRE = 0x46
    CORRECTION = 0x47
    SUITE = 0x48
    CONNEXION_FIN = 0x49


_C0_NAMES = {
    NUL: "NUL",
    BEL: "BEL",
    BS: "BS",
    HT: "HT",
    LF: "LF",
    VT: "VT",
    FF: "FF (clear+home)",
    CR: "CR",
    SO: "SO (semigraphic)",
    SI: "SI (text)",
    CAN: "CAN",
    SUB: "SUB",
    ESC: "ESC",
    SS2: "SS2",
    RS: "RS (home)",
    US: "US (position)",
    SEP: "SEP",
}


def control_name(byte: int) -> str | None:
    """Return a friendly name for a control byte, or ``None`` if it is a plain
    printable character. Used by the (roadmapped) protocol monitor."""
    if byte in _C0_NAMES:
        return _C0_NAMES[byte]
    try:
        return f"KEY {Key(byte).name}"
    except ValueError:
        return None


def function_key_sequence(key: Key) -> bytes:
    """The two bytes a Minitel sends for a function key (``SEP`` + code)."""
    return bytes((SEP, int(key)))
