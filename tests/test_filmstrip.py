from minitel_workbench.monitor.filmstrip import build_filmstrip, frame_screens, split_frames
from minitel_workbench.videotex import constants as C


def _page(text: bytes) -> bytes:
    return bytes([C.FF]) + text


def test_split_frames_on_ff():
    stream = _page(b"ONE") + _page(b"TWO") + _page(b"THREE")
    frames = split_frames(stream)
    assert len(frames) == 3
    assert all(f[0] == C.FF for f in frames)


def test_frame_screens_skips_near_empty():
    stream = _page(b"HELLO WORLD") + _page(b"") + _page(b"SECOND PAGE")
    screens = frame_screens(stream)
    assert len(screens) == 2
    assert "HELLO WORLD" in screens[0].text
    assert "SECOND PAGE" in screens[1].text


def test_build_filmstrip_contains_all_pages():
    stream = _page(b"WEATHER PARIS") + _page(b"NEWS TODAY")
    html = build_filmstrip(stream, title="session")
    assert html.startswith("<!doctype html>")
    assert "WEATHER PARIS" in html
    assert "NEWS TODAY" in html
    assert "2 screens" in html


def test_last_frame_not_the_only_one():
    # Regression for the real bug: the final screen (a screensaver) must not be
    # the only thing you can see — earlier pages survive in the filmstrip.
    stream = _page(b"THE PAGE I WANTED") + _page(b"IDLE SCREENSAVER SMILEY")
    html = build_filmstrip(stream)
    assert "THE PAGE I WANTED" in html
