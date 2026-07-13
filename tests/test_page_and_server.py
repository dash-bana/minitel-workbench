from minitel_workbench.bridge import Bridge
from minitel_workbench.hardware.link import LoopbackLink
from minitel_workbench.transport.menu_server import MenuServerTransport, load_pages_from_dir
from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder
from minitel_workbench.videotex.page import PageSpec, build_page


def render(data: bytes) -> Decoder:
    d = Decoder()
    d.feed(data)
    return d


def test_build_page_title_and_lines():
    spec = PageSpec.from_dict(
        {"title": "METEO", "lines": [{"text": "Ciel clair", "colour": "cyan"}, "18 degres"]}
    )
    d = render(build_page(spec))
    text = d.screen.text
    assert "METEO" in text
    assert "Ciel clair" in text
    assert "18 degres" in text


def test_build_page_applies_colour():
    d = render(build_page({"title": "X", "lines": [{"text": "RED", "colour": "red", "col": 2}]}))
    # find the 'R' of RED and check its attribute
    for r in range(d.screen.rows):
        line = d.screen.line(r)
        if "RED" in line:
            c = line.index("RED")
            assert d.screen.attr(r, c).fg == 1
            break
    else:
        raise AssertionError("RED not found")


def test_build_page_from_dict_accepts_american_spelling():
    d = render(build_page({"title": "T", "lines": [{"text": "Z", "color": "green"}]}))
    assert "Z" in d.screen.text


def _drain(bridge, n=12):
    for _ in range(n):
        bridge.pump(timeout=0.05)


def test_menu_server_serves_pages():
    pages = [
        ("Weather", build_page({"title": "WEATHER", "lines": ["Sunny"]})),
        ("News", build_page({"title": "NEWS", "lines": ["Headline"]})),
    ]
    link = LoopbackLink()
    server = MenuServerTransport(pages, title="HOME")
    decoder = Decoder()
    bridge = Bridge(link, server, monitor=decoder)
    try:
        _drain(bridge)
        assert "HOME" in decoder.screen.text
        assert "Weather" in decoder.screen.text

        link.feed_key(b"2")
        link.feed_key(C.function_key_sequence(C.Key.ENVOI))
        _drain(bridge)
        assert "NEWS" in decoder.screen.text
        assert "Headline" in decoder.screen.text

        link.feed_key(C.function_key_sequence(C.Key.SOMMAIRE))
        _drain(bridge)
        assert "HOME" in decoder.screen.text
    finally:
        bridge.close()


def test_load_pages_from_dir(tmp_path):
    (tmp_path / "b_second.vdt").write_bytes(b"\x0cSECOND")
    (tmp_path / "a_first.vdt").write_bytes(b"\x0cFIRST")
    pages = load_pages_from_dir(str(tmp_path))
    assert [name for name, _ in pages] == ["a_first", "b_second"]  # sorted
    assert pages[0][1] == b"\x0cFIRST"
