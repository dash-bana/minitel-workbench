"""The golden test: the whole data path with no hardware and no network.

LoopbackLink (stands in for the Minitel) <-> Bridge <-> LocalDemoTransport, with a
Decoder tapping the display stream. If this passes, the bridge, a transport, a
link, the Videotex decoder and the screen model all work together.
"""

from minitel_workbench.bridge import Bridge
from minitel_workbench.hardware.link import LoopbackLink
from minitel_workbench.transport.local_demo import LocalDemoTransport
from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder


def drain(bridge, times=12):
    for _ in range(times):
        bridge.pump(timeout=0.05)


def make():
    link = LoopbackLink()
    transport = LocalDemoTransport()
    decoder = Decoder()
    bridge = Bridge(link, transport, monitor=decoder)
    return link, bridge, decoder


def test_home_page_renders():
    link, bridge, decoder = make()
    try:
        drain(bridge)
        assert "MINITEL WORKBENCH" in decoder.screen.text
        assert "POURQUOI CE SERVICE" in decoder.screen.text  # the menu
        # The home page must say what this service is, for someone who is looking
        # at a Minitel rather than at the documentation.
        assert "Aucun reseau" in decoder.screen.text
    finally:
        bridge.close()


def test_navigate_to_info_and_back():
    link, bridge, decoder = make()
    try:
        drain(bridge)
        link.feed_key(b"1")
        link.feed_key(C.function_key_sequence(C.Key.ENVOI))
        drain(bridge)
        text = decoder.screen.text
        assert "POURQUOI CE SERVICE" in text
        assert "reseau" in text  # body of the page
        assert "MIRE" in text  # and it points at the test card

        link.feed_key(C.function_key_sequence(C.Key.SOMMAIRE))
        drain(bridge)
        assert "CODE + ENVOI" in decoder.screen.text
    finally:
        bridge.close()


def test_semigraphic_demo_page_draws_blocks():
    link, bridge, decoder = make()
    try:
        drain(bridge)
        link.feed_key(b"2")
        link.feed_key(C.function_key_sequence(C.Key.ENVOI))
        drain(bridge)
        assert "█" in decoder.screen.text  # mosaic blocks rendered
    finally:
        bridge.close()


def test_colour_page_decodes_attributes():
    link, bridge, decoder = make()
    try:
        drain(bridge)
        link.feed_key(b"4")
        link.feed_key(C.function_key_sequence(C.Key.ENVOI))
        drain(bridge)
        # The colour page prints "RED" in red at row 4 col 6 (internal 3,5).
        assert decoder.screen.glyph(3, 5) == "R"
        assert decoder.screen.attr(3, 5).fg == 1  # red
    finally:
        bridge.close()


def test_typed_characters_are_echoed_by_service():
    link, bridge, decoder = make()
    try:
        drain(bridge)
        # LocalDemo echoes typed chars (the bridge doesn't do local echo).
        link.feed_key(b"9")
        drain(bridge)
        assert link.display  # something came back toward the terminal
    finally:
        bridge.close()
