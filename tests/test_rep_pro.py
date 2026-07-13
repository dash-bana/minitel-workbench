"""REP (run-length) and PRO (protocol) sequences — found in real MiniPavi data."""

from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder
from minitel_workbench.videotex.protocol import describe_stream


def test_rep_repeats_last_glyph():
    d = Decoder()
    # 'X' then REP with count 5 -> six 'X' total.
    d.feed(bytes([C.FF]) + b"X" + bytes([C.REP, C.POS_OFFSET + 5]))
    assert d.screen.line(0).startswith("XXXXXX")


def test_rep_repeats_mosaic_fill():
    d = Decoder()
    d.feed(bytes([C.FF, C.SO, 0x7F, C.REP, C.POS_OFFSET + 3]))  # block + 3 repeats
    assert d.screen.line(0).startswith("████")


def test_pro_sequences_are_not_printed():
    d = Decoder()
    # PRO2 = ESC 0x3A + 2 bytes; must be swallowed, not shown as text "sH".
    d.feed(bytes([C.FF, C.ESC, C.PRO2, 0x73, 0x48]) + b"OK")
    assert d.screen.line(0).startswith("OK")
    assert "s" not in d.screen.line(0)[:2]


def test_pro3_length():
    d = Decoder()
    d.feed(bytes([C.FF, C.ESC, C.PRO3, 0x63, 0x58, 0x49]) + b"Z")
    assert d.screen.line(0).startswith("Z")


def test_inspect_names_rep_and_pro():
    descs = [e.description for e in describe_stream(bytes([C.ESC, C.PRO2, 0x73, 0x48]))]
    assert descs == ["PRO2 protocol sequence"]
    descs = [e.description for e in describe_stream(b"X" + bytes([C.REP, C.POS_OFFSET + 9]))]
    assert any("repeat previous glyph ×9" == d for d in descs)


def test_pro_sequence_split_across_feeds():
    d = Decoder()
    d.feed(bytes([C.FF, C.ESC, C.PRO2, 0x73]))  # missing final param byte
    d.feed(bytes([0x48]) + b"OK")
    assert d.screen.line(0).startswith("OK")
