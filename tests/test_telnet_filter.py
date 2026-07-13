from minitel_workbench.transport.telnet import DO, DONT, IAC, SB, SE, WILL, WONT, TelnetFilter


def _collect():
    sent = []
    return sent, sent.append


def test_plain_bytes_pass_through():
    f = TelnetFilter()
    sent, send = _collect()
    assert f.feed(b"\x0cHELLO", send) == b"\x0cHELLO"
    assert sent == []


def test_iac_iac_becomes_single_ff():
    f = TelnetFilter()
    _, send = _collect()
    assert f.feed(bytes([IAC, IAC, 0x41]), send) == bytes([0xFF, 0x41])


def test_do_option_is_refused_with_wont():
    f = TelnetFilter()
    sent, send = _collect()
    # Server: IAC DO ECHO(1). We must strip it and reply IAC WONT ECHO.
    out = f.feed(bytes([IAC, DO, 1]) + b"AB", send)
    assert out == b"AB"
    assert sent == [bytes([IAC, WONT, 1])]


def test_will_option_is_refused_with_dont():
    f = TelnetFilter()
    sent, send = _collect()
    out = f.feed(bytes([IAC, WILL, 3]), send)
    assert out == b""
    assert sent == [bytes([IAC, DONT, 3])]


def test_sequence_split_across_chunks():
    f = TelnetFilter()
    sent, send = _collect()
    # IAC DO 24 arrives in two pieces.
    assert f.feed(bytes([0x41, IAC, DO]), send) == b"A"
    assert sent == []  # can't reply yet — option byte not seen
    assert f.feed(bytes([24, 0x42]), send) == b"B"
    assert sent == [bytes([IAC, WONT, 24])]


def test_subnegotiation_is_dropped():
    f = TelnetFilter()
    _, send = _collect()
    data = b"X" + bytes([IAC, SB, 24, 1, 2, 3, IAC, SE]) + b"Y"
    assert f.feed(data, send) == b"XY"


def test_videotex_control_bytes_are_untouched():
    f = TelnetFilter()
    _, send = _collect()
    # US position + text must survive verbatim (only 0xFF is special).
    payload = bytes([0x1F, 0x48, 0x53]) + b"OK"
    assert f.feed(payload, send) == payload
