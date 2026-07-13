from minitel_workbench.monitor.screen import COLS, ROWS, Screen


def test_put_and_text():
    s = Screen()
    for ch in "HELLO":
        s.put(ch)
    assert s.line(0).startswith("HELLO")
    assert s.text.splitlines()[0] == "HELLO"


def test_wrap_advances_row():
    s = Screen()
    s.move_to(0, COLS - 1)
    s.put("A")
    s.put("B")
    assert s.line(0)[COLS - 1] == "A"
    assert s.line(1)[0] == "B"
    assert (s.row, s.col) == (1, 1)


def test_clear_resets():
    s = Screen()
    s.put("Z")
    s.clear()
    assert s.text.strip() == ""
    assert (s.row, s.col) == (0, 0)


def test_scroll_on_last_row():
    s = Screen()
    s.move_to(ROWS - 1, 0)
    s.put("A")  # wraps: col back to 0 and scrolls up
    s.cursor_down()
    assert s.rows == ROWS


def test_framed_dimensions():
    s = Screen()
    lines = s.framed().splitlines()
    assert len(lines) == ROWS + 2
    assert all(len(line) == COLS + 2 for line in lines)
