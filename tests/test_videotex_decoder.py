from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder, _mosaic_glyph


def pos(row, col):
    return bytes((C.US, C.POS_OFFSET + row, C.POS_OFFSET + col))


def test_ff_clears_and_homes_then_text():
    d = Decoder()
    d.feed(bytes([C.FF]) + b"HI")
    assert d.screen.line(0).startswith("HI")
    assert d.screen.row == 0 and d.screen.col == 2


def test_us_positioning():
    d = Decoder()
    d.feed(bytes([C.FF]) + pos(3, 5) + b"X")
    # 1-based row 3 col 5 -> internal row 2 col 4.
    assert d.screen.line(2)[4] == "X"


def test_us_split_across_feeds():
    d = Decoder()
    d.feed(bytes([C.FF, C.US, C.POS_OFFSET + 3]))  # incomplete: missing column
    d.feed(bytes([C.POS_OFFSET + 5]) + b"Z")
    assert d.screen.line(2)[4] == "Z"


def test_semigraphic_full_block():
    d = Decoder()
    d.feed(bytes([C.FF, C.SO, 0x7F, C.SI]))
    assert d.screen.line(0)[0] == "█"


def test_mosaic_glyph_edges():
    assert _mosaic_glyph(0x20) == " "  # pattern 0 -> blank
    assert _mosaic_glyph(0x7F) == "█"  # pattern 63 -> full block


def test_g2_acute_accent_composes():
    d = Decoder()
    d.feed(bytes([C.FF, C.SS2, 0x42]) + b"e")  # acute + e -> é
    assert d.screen.line(0)[0] == "é"


def test_unknown_bytes_never_raise():
    d = Decoder()
    d.feed(bytes(range(0, 32)) + bytes([C.ESC, 0x50]) + b"ok")
    assert "ok" in d.screen.text
