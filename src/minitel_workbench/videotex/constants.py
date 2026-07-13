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
REP = 0x12  # repeat previous glyph: REP <0x40+count>
CURSOR_ON = 0x11  # DC1 — show cursor
CURSOR_OFF = 0x14  # DC4 — hide cursor

# Minitel protocol sequences: ESC followed by one of these, then N param bytes.
PRO1 = 0x39
PRO2 = 0x3A
PRO3 = 0x3B
_PRO_PARAM_LEN = {PRO1: 1, PRO2: 2, PRO3: 3}


def pro_param_len(code: int) -> int | None:
    """Number of parameter bytes after ``ESC <code>`` for a PRO sequence, or None."""
    return _PRO_PARAM_LEN.get(code)


# --- Local echo control (PRO3 "aiguillage" / routing) ----------------------
# The Minitel can loop the keyboard straight to its own screen (local echo). When
# the remote service also echoes (MiniPavi, Retrocampus do), that doubles every
# character. Disabling the screen<-keyboard routing leaves keyboard->peripheral
# and peripheral->screen intact, so keystrokes still reach the host and the
# service's echo still shows — just once.
_AIGUILLAGE_OFF = 0x60
_AIGUILLAGE_ON = 0x61
_RECEPTION_ECRAN = 0x58  # screen as receiver
_EMISSION_CLAVIER = 0x51  # keyboard as emitter

LOCAL_ECHO_OFF = bytes((ESC, PRO3, _AIGUILLAGE_OFF, _RECEPTION_ECRAN, _EMISSION_CLAVIER))
LOCAL_ECHO_ON = bytes((ESC, PRO3, _AIGUILLAGE_ON, _RECEPTION_ECRAN, _EMISSION_CLAVIER))


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


# --- CEPT / Teletel colour + attribute set (C1, introduced by ESC) ---------
#
# Colour index order matches ANSI (0 black … 7 white), which makes ANSI SGR
# rendering a direct offset. Attributes below are the codes that follow ESC
# (0x1B) in the Minitel alphanumeric/graphic sets.

COLOURS = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
)

# ESC <code> ranges/values:
ATTR_FG_BASE = 0x40  # 0x40..0x47 -> foreground colour 0..7
ATTR_BG_BASE = 0x50  # 0x50..0x57 -> background colour 0..7
ATTR_BLINK_ON = 0x48
ATTR_BLINK_OFF = 0x49
ATTR_SIZE_NORMAL = 0x4C
ATTR_SIZE_DOUBLE_HEIGHT = 0x4D
ATTR_SIZE_DOUBLE_WIDTH = 0x4E
ATTR_SIZE_DOUBLE = 0x4F
ATTR_CONCEAL_ON = 0x58
ATTR_UNDERLINE_OFF = 0x59  # end lining / underline
ATTR_UNDERLINE_ON = 0x5A  # start lining / underline
ATTR_INVERSE_OFF = 0x5C  # background normal
ATTR_INVERSE_ON = 0x5D  # inverted background/foreground
ATTR_CONCEAL_OFF = 0x5F


def esc(code: int) -> bytes:
    """An attribute sequence: ESC + ``code``."""
    return bytes((ESC, code))


def set_foreground(colour: int) -> bytes:
    return esc(ATTR_FG_BASE + (colour & 0x07))


def set_background(colour: int) -> bytes:
    return esc(ATTR_BG_BASE + (colour & 0x07))
