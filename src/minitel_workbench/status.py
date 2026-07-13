"""Service status monitor — is a destination reachable right now?

Runs entirely from the Mac, needs no Minitel, and (per Constitution rule II) is
useful to telephone-only users and to people without a terminal at all. It does a
lightweight TCP connect to a service's host:port as a liveness proxy — it does not
log in or send data, and it is dependency-free (no ``websocket-client`` needed to
tell whether the server is listening).

`check_all` performs outbound network connections when *you* run it; nothing is
contacted at import time or during tests.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import urlsplit

from .services import Service, ServiceDirectory

ONLINE = "online"
OFFLINE = "offline"
UNKNOWN = "unknown"

_DEFAULT_PORTS = {"ws": 80, "wss": 443, "http": 80, "https": 443}


@dataclass
class ServiceStatus:
    service_id: str
    name: str
    state: str  # ONLINE | OFFLINE | UNKNOWN
    detail: str = ""


def _endpoint(access: dict) -> tuple[str, int] | None:
    """Derive a (host, port) to probe from an access record, or None."""
    kind = access.get("kind")
    if kind in ("telnet", "tcp"):
        return access["host"], int(access["port"])
    if kind in ("websocket", "ws"):
        parts = urlsplit(access["url"])
        if not parts.hostname:
            return None
        port = parts.port or _DEFAULT_PORTS.get(parts.scheme, 80)
        return parts.hostname, port
    return None


def check_service(svc: Service, timeout: float = 5.0) -> ServiceStatus:
    """Probe one service. Never raises."""
    if svc.transport_kind == "demo":
        return ServiceStatus(svc.id, svc.name, ONLINE, "offline demo — always available")
    if svc.transport_kind == "telephone":
        return ServiceStatus(svc.id, svc.name, UNKNOWN, "telephone service — dial to reach it")

    endpoint = _endpoint(svc.access)
    if endpoint is None:
        return ServiceStatus(svc.id, svc.name, UNKNOWN, "no reachable endpoint to probe")

    host, port = endpoint
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ServiceStatus(svc.id, svc.name, ONLINE, f"{host}:{port} reachable")
    except OSError as exc:
        return ServiceStatus(svc.id, svc.name, OFFLINE, f"{host}:{port} — {exc.__class__.__name__}")


def check_all(directory: ServiceDirectory, timeout: float = 5.0) -> list[ServiceStatus]:
    """Probe every service concurrently, preserving directory order."""
    services = directory.all()
    if not services:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(services))) as pool:
        return list(pool.map(lambda s: check_service(s, timeout), services))
