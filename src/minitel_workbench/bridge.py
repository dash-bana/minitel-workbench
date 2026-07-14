"""The bridge: pump bytes between a Minitel ``Link`` and a service ``Transport``.

This is the piece the whole design converged on. The original GUI bridge routed
every byte through a Tkinter/Twisted event loop and stalled; the fix was a direct
forwarding loop with nothing in the hot path. That is exactly this class. Optional
*taps* — a recorder and a display monitor — observe the streams without slowing
them, because they only ever append to buffers.
"""

from __future__ import annotations

import select
from collections.abc import Callable

from .channel import ByteChannel, ChannelClosed


class Bridge:
    """Forward bytes both ways between one ``Link`` and one ``Transport``."""

    def __init__(
        self,
        link: ByteChannel,
        transport: ByteChannel,
        *,
        recorder: object | None = None,
        monitor: object | None = None,
        close_link: bool = True,
        close_recorder: bool = True,
    ) -> None:
        self.link = link
        self.transport = transport
        self.recorder = recorder
        self.monitor = monitor
        # When reconnecting, the caller reuses one link and one recorder across
        # many transports, so a per-session Bridge must not close them.
        self._close_link = close_link
        self._close_recorder = close_recorder
        self._closed = False

    def pump(self, timeout: float = 0.1) -> bool:
        """Run one ``select`` iteration. Returns ``False`` once the session ends.

        Safe to call repeatedly; this is how tests drive the bridge deterministically.
        """
        if self._closed:
            return False

        try:
            readable, _, _ = select.select(
                [self.link.fileno(), self.transport.fileno()], [], [], timeout
            )
        except (ValueError, OSError):
            # A descriptor was closed underneath us.
            self.close()
            return False

        for fd in readable:
            if fd == self.link.fileno():
                if not self._forward_from_terminal():
                    return not self._closed
            else:
                if not self._forward_from_service():
                    return not self._closed
        return True

    def _forward_from_terminal(self) -> bool:
        try:
            data = self.link.read()
        except (ChannelClosed, OSError):
            # OSError: the descriptor was closed under us mid-pump (EBADF).
            self.close()
            return False
        if data:
            self.transport.write(data)
            if self.recorder is not None:
                self.recorder.from_terminal(data)
        return True

    def _forward_from_service(self) -> bool:
        try:
            data = self.transport.read()
        except (ChannelClosed, OSError):
            self.close()
            return False
        if data:
            self.link.write(data)
            if self.recorder is not None:
                self.recorder.from_service(data)
            if self.monitor is not None:
                self.monitor.feed(data)
        return True

    def run(self, should_continue: Callable[[], bool] = lambda: True, timeout: float = 0.1) -> None:
        """Pump until the session closes or ``should_continue()`` returns False."""
        try:
            while should_continue() and self.pump(timeout):
                pass
        finally:
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.transport.close()
        if self._close_link:
            self.link.close()
        if self._close_recorder and self.recorder is not None:
            close = getattr(self.recorder, "close", None)
            if callable(close):
                close()

    @property
    def closed(self) -> bool:
        return self._closed
