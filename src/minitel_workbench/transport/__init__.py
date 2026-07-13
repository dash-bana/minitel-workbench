"""The service side: TCP/Telnet, WebSocket, and an offline demo service.

A ``Transport`` is just a :class:`~minitel_workbench.channel.ByteChannel`. The
:func:`build_transport` factory turns a service's ``access`` record (from the
directory) into the right transport, so nothing above this layer needs to know
whether "Retrocampus" means a WebSocket or a phone number.
"""

from __future__ import annotations

from ..channel import ByteChannel
from .local_demo import LocalDemoTransport
from .tcp import TcpTransport
from .telnet import TelnetFilter

__all__ = [
    "ByteChannel",
    "TcpTransport",
    "TelnetFilter",
    "LocalDemoTransport",
    "build_transport",
]


class UnsupportedTransport(Exception):
    """Raised when a service's access method has no usable transport here.

    Deliberately actionable (Constitution rule VI): telephone services, for
    instance, point the user at the dialing assistant rather than erroring
    obscurely.
    """


def build_transport(access: dict, *, name: str = "service") -> ByteChannel:
    """Create a transport for a directory ``access`` record.

    ``access`` looks like ``{"kind": "telnet", "host": ..., "port": ...}`` or
    ``{"kind": "websocket", "url": ...}`` or ``{"kind": "demo"}``.
    """
    kind = access.get("kind")
    if kind in ("telnet", "tcp"):
        return TcpTransport(
            access["host"],
            int(access["port"]),
            telnet=(kind == "telnet"),
            name=name,
        )
    if kind in ("websocket", "ws"):
        from .websocket import WebSocketTransport  # lazy: optional dependency

        return WebSocketTransport(access["url"], name=name)
    if kind == "demo":
        return LocalDemoTransport(name=name)
    if kind == "telephone":
        raise UnsupportedTransport(
            f"{name} is a telephone service — dial it on the Minitel itself. "
            "See the dialing assistant (roadmap 0.8)."
        )
    raise UnsupportedTransport(f"Don't know how to connect to {name!r} (kind={kind!r}).")
