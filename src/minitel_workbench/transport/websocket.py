"""WebSocket transport for ``ws://`` / ``wss://`` services (e.g. Retrocampus).

The design notebook noted that the community's ``ws``-only servers can't be
reached by a plain telnet client. This closes that gap — and, crucially, lets
Retrocampus be the *featured default* (Constitution: featured destinations)
rather than an also-ran.

WebSocket framing is inherently message-based, not a raw fd, so we run the socket
in a worker thread and expose an ``os.pipe`` read-end. That keeps the transport
``select()``-able exactly like the serial link and the TCP transport, so the
bridge stays transport-agnostic.
"""

from __future__ import annotations

import os
import threading

from ..channel import ByteChannel, ChannelClosed


class WebSocketTransport(ByteChannel):
    """A ``ws``/``wss`` connection presented as a selectable byte channel."""

    def __init__(self, url: str, *, name: str = "service", connect_timeout: float = 15.0) -> None:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                f"Connecting to {name} needs the optional 'websocket-client' package.\n"
                'Install it with:  python -m pip install "minitel-workbench[ws]"'
            ) from exc

        self.name = name
        self.url = url
        self._abnf = websocket.ABNF
        self._ws = websocket.create_connection(url, timeout=connect_timeout)
        self._ws.settimeout(None)  # blocking recv inside the reader thread
        self._rx_r, self._rx_w = os.pipe()
        os.set_blocking(self._rx_r, False)
        self._closed = False
        self._reader = threading.Thread(target=self._pump, name=f"ws-rx:{name}", daemon=True)
        self._reader.start()

    def _pump(self) -> None:
        """Read frames off the socket and shovel their bytes into the pipe."""
        try:
            while not self._closed:
                opcode, data = self._ws.recv_data(control_frame=False)
                if opcode == self._abnf.OPCODE_CLOSE:
                    break
                if not data:
                    continue
                if isinstance(data, str):
                    data = data.encode("latin-1", "replace")
                os.write(self._rx_w, data)
        except Exception:
            pass
        finally:
            try:
                os.close(self._rx_w)
            except OSError:
                pass

    def fileno(self) -> int:
        return self._rx_r

    def read(self, size: int = 4096) -> bytes:
        try:
            data = os.read(self._rx_r, size)
        except BlockingIOError:
            return b""
        if data == b"":
            raise ChannelClosed
        return data

    def write(self, data: bytes) -> None:
        self._ws.send(data, opcode=self._abnf.OPCODE_BINARY)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._ws.close()
        except Exception:
            pass
        try:
            os.close(self._rx_r)
        except OSError:
            pass
