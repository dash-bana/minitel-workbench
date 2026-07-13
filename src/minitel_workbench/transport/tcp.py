"""Raw TCP and Telnet transports.

Covers MiniPavi (`go.minipavi.fr:516`, telnet) and any plain videotex host. The
socket is non-blocking so the bridge's ``select()`` loop drives it uniformly with
the serial link.
"""

from __future__ import annotations

import socket

from ..channel import ByteChannel, ChannelClosed
from .telnet import TelnetFilter


class TcpTransport(ByteChannel):
    """A TCP connection to a videotex service, optionally Telnet-filtered."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        telnet: bool = True,
        name: str = "service",
        connect_timeout: float = 15.0,
    ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self._sock = socket.create_connection((host, port), timeout=connect_timeout)
        # Detect a silently dropped connection so auto-reconnect can kick in.
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._sock.setblocking(False)
        self._filter = TelnetFilter() if telnet else None

    def fileno(self) -> int:
        return self._sock.fileno()

    def read(self, size: int = 4096) -> bytes:
        try:
            data = self._sock.recv(size)
        except (BlockingIOError, InterruptedError):
            return b""
        if data == b"":
            raise ChannelClosed
        if self._filter is not None:
            return self._filter.feed(data, self._sock.sendall)
        return data

    def write(self, data: bytes) -> None:
        self._sock.sendall(data)

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass
