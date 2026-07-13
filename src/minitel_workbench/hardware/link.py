"""Links: the Minitel-facing end of a session.

``SerialLink`` talks to a real terminal over a USB serial adapter; ``pyserial``
is imported lazily so the rest of the app never depends on it. ``LoopbackLink``
is an in-process stand-in used by the test suite and (later) the emulator to
inject keystrokes and capture what would be displayed — no hardware required.
"""

from __future__ import annotations

import os

from ..channel import ByteChannel, ChannelClosed
from .capability import CapabilityProfile, profile_for_model

_PARITY_MAP = {"even": "E", "odd": "O", "none": "N"}


class SerialLink(ByteChannel):
    """A real Minitel over a USB serial adapter (1200 7E1 by default)."""

    name = "Minitel"

    def __init__(self, serial_port: object, profile: CapabilityProfile) -> None:
        self._ser = serial_port
        self.profile = profile

    @classmethod
    def open(
        cls,
        device: str,
        profile: CapabilityProfile | None = None,
        *,
        speed: int | None = None,
    ) -> SerialLink:
        """Open ``device`` with Minitel framing. Raises a clear error if
        ``pyserial`` is missing — never an obscure ImportError at startup."""
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised only w/o pyserial
            raise RuntimeError(
                "Talking to a real Minitel needs the optional 'pyserial' package.\n"
                'Install it with:  python -m pip install "minitel-workbench[serial]"'
            ) from exc

        prof = profile or profile_for_model(None)
        parity = {
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD,
            "none": serial.PARITY_NONE,
        }[prof.parity]
        bytesize = {7: serial.SEVENBITS, 8: serial.EIGHTBITS}[prof.data_bits]
        stopbits = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}[prof.stop_bits]

        ser = serial.Serial(
            port=device,
            baudrate=speed or prof.default_speed,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=0,  # non-blocking reads, so the bridge's select() drives us
            write_timeout=2,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        return cls(ser, prof)

    def fileno(self) -> int:
        return self._ser.fileno()

    def read(self, size: int = 4096) -> bytes:
        waiting = getattr(self._ser, "in_waiting", 0)
        return self._ser.read(waiting or 1) if waiting else self._ser.read(size)

    def write(self, data: bytes) -> None:
        self._ser.write(data)
        self._ser.flush()

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass


class LoopbackLink(ByteChannel):
    """An in-process Minitel stand-in.

    ``feed_key(...)`` injects bytes as if typed on the keyboard; everything the
    bridge writes toward the terminal is captured in :attr:`display`.
    """

    name = "Minitel (loopback)"

    def __init__(self) -> None:
        self._kbd_r, self._kbd_w = os.pipe()
        os.set_blocking(self._kbd_r, False)
        self.display = bytearray()
        self._closed = False

    def feed_key(self, data: bytes) -> None:
        """Simulate keystrokes arriving from the Minitel keyboard."""
        os.write(self._kbd_w, data)

    def fileno(self) -> int:
        return self._kbd_r

    def read(self, size: int = 4096) -> bytes:
        try:
            data = os.read(self._kbd_r, size)
        except BlockingIOError:
            return b""
        if data == b"" and self._closed:
            raise ChannelClosed
        return data

    def write(self, data: bytes) -> None:
        self.display.extend(data)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for fd in (self._kbd_r, self._kbd_w):
            try:
                os.close(fd)
            except OSError:
                pass
