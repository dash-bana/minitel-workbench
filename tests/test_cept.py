"""CEPT level-2 attribute decoding and rendering."""

from minitel_workbench.monitor.screen import Attr, Screen
from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder


def feed(*parts: bytes) -> Decoder:
    d = Decoder()
    d.feed(bytes([C.FF]) + b"".join(parts))
    return d


def test_foreground_colour():
    d = feed(C.set_foreground(1), b"X")  # red
    assert d.screen.glyph(0, 0) == "X"
    assert d.screen.attr(0, 0).fg == 1


def test_background_colour():
    d = feed(C.set_background(2), b"X")  # green bg
    assert d.screen.attr(0, 0).bg == 2


def test_blink_toggles():
    d = feed(C.esc(C.ATTR_BLINK_ON), b"A", C.esc(C.ATTR_BLINK_OFF), b"B")
    assert d.screen.attr(0, 0).blink is True
    assert d.screen.attr(0, 1).blink is False


def test_inverse_swaps_effective_colours():
    d = feed(C.set_foreground(6), C.esc(C.ATTR_INVERSE_ON), b"A")
    a = d.screen.attr(0, 0)
    assert a.inverse is True
    assert a.effective_fg == a.bg and a.effective_bg == 6


def test_conceal_and_underline_and_size():
    d = feed(
        C.esc(C.ATTR_CONCEAL_ON),
        C.esc(C.ATTR_UNDERLINE_ON),
        C.esc(C.ATTR_SIZE_DOUBLE_HEIGHT),
        b"A",
    )
    a = d.screen.attr(0, 0)
    assert a.conceal and a.underline and a.double_height


def test_mosaic_pen_marks_cell():
    d = feed(bytes([C.SO]), bytes([0x7F]))
    assert d.screen.attr(0, 0).mosaic is True


def test_clear_resets_pen():
    d = Decoder()
    d.feed(bytes([C.FF]) + C.set_foreground(1) + b"A" + bytes([C.FF]) + b"B")
    # After the second FF, the pen is back to default (white on black).
    assert d.screen.attr(0, 0) == Attr()
    assert d.screen.glyph(0, 0) == "B"


def test_to_ansi_contains_escape_and_reset():
    s = Screen()
    s.set_pen(fg=1)
    s.put("A")
    ansi = s.to_ansi()
    assert "\x1b[" in ansi and "31" in ansi  # red foreground SGR
    assert ansi.rstrip().endswith("\x1b[0m")


def test_to_html_is_selfcontained_and_coloured():
    s = Screen()
    s.set_pen(fg=1)
    s.put("A")
    doc = s.to_html()
    assert doc.startswith("<!doctype html>")
    assert "<pre" in doc and "<span" in doc
    assert "#ff5555" in doc  # red used somewhere
