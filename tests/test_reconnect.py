"""Bridge lifecycle options that make auto-reconnect possible."""

from minitel_workbench.bridge import Bridge
from minitel_workbench.hardware.link import LoopbackLink
from minitel_workbench.transport.local_demo import LocalDemoTransport


def test_close_link_false_keeps_link_open_for_reuse():
    link = LoopbackLink()
    t1 = LocalDemoTransport()
    b1 = Bridge(link, t1, close_link=False)
    for _ in range(8):
        b1.pump(timeout=0.02)
    b1.close()
    assert b1.closed
    assert not link._closed, "link must survive a per-session bridge close"

    # A second session can reuse the same link.
    t2 = LocalDemoTransport()
    b2 = Bridge(link, t2, close_link=False)
    for _ in range(8):
        b2.pump(timeout=0.02)
    b2.close()
    assert not link._closed
    link.close()
    assert link._closed


def test_default_close_still_closes_link():
    link = LoopbackLink()
    t = LocalDemoTransport()
    b = Bridge(link, t)
    b.close()
    assert link._closed


class _CountingRecorder:
    def __init__(self):
        self.closed = 0

    def from_terminal(self, data):
        pass

    def from_service(self, data):
        pass

    def close(self):
        self.closed += 1


def test_close_recorder_false_preserves_recorder():
    link = LoopbackLink()
    rec = _CountingRecorder()
    b = Bridge(link, LocalDemoTransport(), recorder=rec, close_link=False, close_recorder=False)
    b.close()
    assert rec.closed == 0  # caller owns the recorder across reconnects
