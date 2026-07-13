from minitel_workbench.monitor.canvas_render import cell_draw_ops
from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder

WHITE = "#e0e0e0"
RED = "#ff5555"


def test_mosaic_pattern_is_preserved_by_the_decoder():
    d = Decoder()
    d.feed(bytes([C.FF, C.SO, 0x7F]))  # full block
    assert d.screen.mosaic_pattern(0, 0) == 0x3F
    t = Decoder()
    t.feed(bytes([C.FF]) + b"A")
    assert t.screen.mosaic_pattern(0, 0) is None


def test_full_mosaic_draws_six_subblocks():
    d = Decoder()
    d.feed(bytes([C.FF, C.SO, 0x7F]))
    ops = cell_draw_ops(d.screen, 12, 18)
    fg_rects = [o for o in ops if o[0] == "rect" and o[5] == WHITE]
    assert len(fg_rects) == 6  # all six sub-cells filled


def test_partial_mosaic_draws_only_set_bits():
    d = Decoder()
    # 0x20 -> pattern bit0 (top-left) only: (0x20&0x1f=0)|((0x20&0x40)>>1=0)=0 -> blank;
    # use 0x21 -> (0x21&0x1f=1) -> bit0 top-left only.
    d.feed(bytes([C.FF, C.SO, 0x21]))
    assert d.screen.mosaic_pattern(0, 0) == 0x01
    ops = cell_draw_ops(d.screen, 12, 18)
    assert len([o for o in ops if o[0] == "rect" and o[5] == WHITE]) == 1


def test_text_cell_emits_a_text_op():
    d = Decoder()
    d.feed(bytes([C.FF]) + b"A")
    ops = cell_draw_ops(d.screen, 12, 18)
    assert [o for o in ops if o[0] == "text" and o[3] == "A"]


def test_coloured_mosaic_uses_the_pen_colour():
    d = Decoder()
    d.feed(bytes([C.FF]) + C.set_foreground(1) + bytes([C.SO, 0x7F]))  # red full block
    ops = cell_draw_ops(d.screen, 12, 18)
    assert len([o for o in ops if o[0] == "rect" and o[5] == RED]) == 6


def test_blank_black_screen_emits_no_rects():
    d = Decoder()
    d.feed(bytes([C.FF]))
    ops = cell_draw_ops(d.screen, 10, 10)
    assert [o for o in ops if o[0] == "rect"] == []  # black bg is not painted
