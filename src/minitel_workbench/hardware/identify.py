"""Ask the Minitel what it is (PRO1 ENQROM).

``ESC 39 7B`` makes the terminal report its ROM signature: five bytes,
``SOH <constructor> <model> <version> EOT``. The letter codes are what the
manufacturer burned in — so this is the terminal's own answer, not a guess from
the serial port's name.

The code tables below are transcribed from Zigazou's PyMinitel
(https://github.com/Zigazou/PyMinitel, ``minitel/constantes.py``), the reference
implementation for this protocol. An unknown code is reported *as* unknown, with
the raw bytes: telling someone they own the wrong machine is worse than telling
them nothing. A first-generation Minitel 1 may not answer at all — that is not a
failure, and :func:`identify` simply returns ``None``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from ..videotex import constants as C

ENQROM = 0x7B
ENQROM_QUERY = bytes((C.ESC, C.PRO1, ENQROM))

SOH = 0x01
EOT = 0x04

CONSTRUCTORS: dict[str, str] = {
    "A": "Matra",
    "B": "RTIC",
    "C": "Telic-Alcatel",
    "D": "Thomson",
    "E": "CCS",
    "F": "Fiet",
    "G": "Fime",
    "H": "Unitel",
    "I": "Option",
    "J": "Bull",
    "K": "Télématique",
    "L": "Desmet",
}


@dataclass(frozen=True)
class ModelSpec:
    name: str
    reversible: bool  # "retournable" — the modem can be reversed
    keyboard: str | None
    max_speed: int
    cols80: bool
    drcs: bool  # downloadable character sets


MODELS: dict[str, ModelSpec] = {
    "b": ModelSpec("Minitel 1", False, "ABCD", 1200, False, False),
    "c": ModelSpec("Minitel 1", False, "Azerty", 1200, False, False),
    "d": ModelSpec("Minitel 10", False, "Azerty", 1200, False, False),
    "e": ModelSpec("Minitel 1 couleur", False, "Azerty", 1200, False, False),
    "f": ModelSpec("Minitel 10", True, "Azerty", 1200, False, False),
    "g": ModelSpec("Émulateur", True, "Azerty", 9600, True, True),
    "j": ModelSpec("Imprimante", False, None, 1200, False, False),
    "r": ModelSpec("Minitel 1", True, "Azerty", 1200, False, False),
    "s": ModelSpec("Minitel 1 couleur", True, "Azerty", 1200, False, False),
    "t": ModelSpec("Terminatel 252", False, None, 1200, False, False),
    "u": ModelSpec("Minitel 1B", True, "Azerty", 4800, True, False),
    "v": ModelSpec("Minitel 2", True, "Azerty", 9600, True, True),
    "w": ModelSpec("Minitel 10B", True, "Azerty", 4800, True, False),
    "y": ModelSpec("Minitel 5", True, "Azerty", 9600, True, True),
    "z": ModelSpec("Minitel 12", True, "Azerty", 9600, True, True),
}


@dataclass(frozen=True)
class Identity:
    """What the terminal said about itself."""

    raw: bytes
    constructor_code: str
    model_code: str
    version: str
    constructor: str | None  # None when the code is not in the published table
    model: ModelSpec | None

    @property
    def summary(self) -> str:
        maker = self.constructor or f"unknown maker '{self.constructor_code}'"
        name = self.model.name if self.model else f"unknown model '{self.model_code}'"
        return f"{maker} {name} (ROM version '{self.version}')"


def _decode(reply: bytes) -> Identity | None:
    if len(reply) != 5 or reply[0] != SOH or reply[4] != EOT:
        return None
    constructor_code = chr(reply[1])
    model_code = chr(reply[2])
    version = chr(reply[3])
    constructor = CONSTRUCTORS.get(constructor_code)

    # Two corrections PyMinitel carries, from terminals seen in the wild.
    if constructor_code == "B" and model_code == "v":
        constructor = "Philips"
    elif constructor_code == "C" and version in ("4", "5", ";", "<"):
        constructor = "Telic ou Matra"

    return Identity(
        raw=reply,
        constructor_code=constructor_code,
        model_code=model_code,
        version=version,
        constructor=constructor,
        model=MODELS.get(model_code),
    )


def identify(link, *, timeout: float = 2.0) -> Identity | None:
    """Ask an open link what terminal is on the other end.

    Returns ``None`` if it does not answer in ``timeout`` seconds, or answers
    with something that is not a ROM signature — both of which are ordinary
    outcomes on an early Minitel, not errors.
    """
    try:
        link.write(ENQROM_QUERY)
    except OSError:
        return None

    reply = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and len(reply) < 5:
        try:
            chunk = link.read(5 - len(reply))
        except OSError:
            return None
        if chunk:
            reply.extend(chunk)
            continue
        time.sleep(0.05)

    return _decode(bytes(reply))
