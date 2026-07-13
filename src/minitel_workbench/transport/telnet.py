"""A conservative Telnet negotiation filter.

Minitel services reached over "telnet" (e.g. MiniPavi on ``go.minipavi.fr:516``)
speak raw Videotex with occasional Telnet option negotiation mixed in. We must
strip that negotiation before it reaches the terminal — otherwise the FF/US/etc.
bytes get corrupted — while politely refusing every option (WONT/DONT). This is
the filter proven in the design notebook, hardened to (a) survive sequences that
straddle read boundaries and (b) skip sub-negotiation blocks.
"""

from __future__ import annotations

from collections.abc import Callable

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250  # begin sub-negotiation
SE = 240  # end sub-negotiation

_NEGOTIATION = (DO, DONT, WILL, WONT)


class TelnetFilter:
    """Stateful stripper. Feed it raw bytes; get back display bytes.

    Any reply the protocol requires (refusing options) is emitted via the
    ``send`` callback passed to :meth:`feed`.
    """

    def __init__(self) -> None:
        self._pending = bytearray()  # incomplete IAC sequence carried over
        self._in_subneg = False

    def feed(self, data: bytes, send: Callable[[bytes], None]) -> bytes:
        buf = self._pending + data
        self._pending = bytearray()
        out = bytearray()
        i = 0
        n = len(buf)

        while i < n:
            byte = buf[i]

            if self._in_subneg:
                # Skip everything until IAC SE. Handle the IAC boundary.
                if byte == IAC:
                    if i + 1 >= n:
                        self._pending = bytearray(buf[i:])
                        break
                    if buf[i + 1] == SE:
                        self._in_subneg = False
                        i += 2
                        continue
                    # IAC IAC inside SB, or stray — skip both bytes.
                    i += 2
                    continue
                i += 1
                continue

            if byte != IAC:
                out.append(byte)
                i += 1
                continue

            # byte == IAC
            if i + 1 >= n:
                self._pending = bytearray(buf[i:])
                break

            command = buf[i + 1]

            if command == IAC:  # escaped literal 0xFF
                out.append(IAC)
                i += 2
                continue

            if command == SB:
                self._in_subneg = True
                i += 2
                continue

            if command in _NEGOTIATION:
                if i + 2 >= n:
                    self._pending = bytearray(buf[i:])
                    break
                option = buf[i + 2]
                # Refuse everything: they offer WILL/DO -> we say DONT/WONT.
                if command in (DO, DONT):
                    send(bytes((IAC, WONT, option)))
                else:  # WILL / WONT
                    send(bytes((IAC, DONT, option)))
                i += 3
                continue

            # Any other 2-byte command (NOP, GA, ...): drop it.
            i += 2

        return bytes(out)
