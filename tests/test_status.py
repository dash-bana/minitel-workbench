"""Status checks run against localhost sockets only — never the live network."""

import socket
import threading

from minitel_workbench.services import Service
from minitel_workbench.status import OFFLINE, ONLINE, UNKNOWN, check_service


def _listening_port() -> tuple[socket.socket, int]:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def _accept_loop():
        try:
            while True:
                conn, _ = srv.accept()
                conn.close()
        except OSError:
            pass

    threading.Thread(target=_accept_loop, daemon=True).start()
    return srv, port


def test_tcp_online():
    srv, port = _listening_port()
    try:
        svc = Service(
            id="t", name="T", access={"kind": "telnet", "host": "127.0.0.1", "port": port}
        )
        st = check_service(svc, timeout=2.0)
        assert st.state == ONLINE
    finally:
        srv.close()


def test_tcp_offline_on_closed_port():
    # Bind then close to get a port that is (almost certainly) not listening.
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    svc = Service(id="t", name="T", access={"kind": "telnet", "host": "127.0.0.1", "port": port})
    st = check_service(svc, timeout=1.0)
    assert st.state == OFFLINE


def test_demo_always_online():
    svc = Service(id="demo", name="Demo", access={"kind": "demo"})
    assert check_service(svc).state == ONLINE


def test_telephone_is_unknown():
    svc = Service(id="p", name="P", access={"kind": "telephone", "number": "01 00 00 00 00"})
    assert check_service(svc).state == UNKNOWN


def test_websocket_endpoint_probe_online():
    srv, port = _listening_port()
    try:
        svc = Service(
            id="w", name="W", access={"kind": "websocket", "url": f"ws://127.0.0.1:{port}"}
        )
        assert check_service(svc, timeout=2.0).state == ONLINE
    finally:
        srv.close()
