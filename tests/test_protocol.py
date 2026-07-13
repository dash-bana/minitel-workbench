from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.protocol import describe_stream, format_events


def descs(data):
    return [e.description for e in describe_stream(data)]


def test_cursor_position_reads_like_the_notebook():
    # 1F 48 53  ->  cursor -> row 8 col 19   (the exact example from the notebook)
    events = describe_stream(bytes([C.US, 0x48, 0x53]))
    assert events[0].description == "cursor → row 8 col 19"


def test_function_key_named():
    assert descs(C.function_key_sequence(C.Key.ENVOI)) == ["KEY ENVOI"]


def test_text_runs_are_grouped():
    events = describe_stream(b"HI" + bytes([C.CR]) + b"YO")
    assert events[0].description == "text 'HI'"
    assert any("CR" in e.description for e in events)
    assert events[-1].description == "text 'YO'"


def test_attribute_escapes_named():
    d = descs(C.set_foreground(1) + C.esc(C.ATTR_BLINK_ON))
    assert d == ["foreground red", "blink on"]


def test_clear_and_semigraphic_controls():
    d = descs(bytes([C.FF, C.SO, C.SI]))
    assert "FF (clear+home)" in d[0]
    assert any("semigraphic" in x for x in d)


def test_format_events_is_aligned_text():
    out = format_events(describe_stream(b"AB"))
    assert "text 'AB'" in out
    assert out.startswith("  ")


def test_offsets_are_correct():
    events = describe_stream(b"A" + bytes([C.FF]) + b"B")
    assert events[0].offset == 0
    assert events[1].offset == 1  # FF right after 'A'
    assert events[2].offset == 2  # 'B'
