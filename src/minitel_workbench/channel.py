"""The one interface the bridge talks to.

Both sides of a session — the Minitel-facing ``Link`` and the service-facing
``Transport`` — are *selectable byte channels*. Keeping them to this tiny surface
is what lets a single ``select()`` loop drive any combination (serial, TCP,
WebSocket, in-process demo) without the bridge knowing which is which. That, in
turn, is what keeps transport out of the user's face (Constitution rule III).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ByteChannel(ABC):
    """A non-blocking, ``select()``-able bidirectional stream of bytes."""

    #: Human-facing label, e.g. "Minitel" or "Retrocampus" — never jargon.
    name: str = "channel"

    @abstractmethod
    def fileno(self) -> int:
        """A file descriptor usable with ``select.select``."""

    @abstractmethod
    def read(self, size: int = 4096) -> bytes:
        """Read up to ``size`` bytes. Returns ``b""`` if nothing is ready, or
        raises :class:`ChannelClosed` if the peer has gone away."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """Write all of ``data`` toward the peer."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying resource. Idempotent."""

    def __enter__(self) -> ByteChannel:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class ChannelClosed(Exception):
    """Raised by :meth:`ByteChannel.read` when the peer has closed the stream."""
