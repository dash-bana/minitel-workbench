"""The GUI controller, tested with no display and no hardware.

It drives the real bridge to the offline demo, so these exercise the same code
the window will run — only the Tk rendering is left unverified here.
"""

import time

from minitel_workbench.gui.controller import WorkbenchController


def _wait(cond, timeout=4.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_connect_demo_updates_the_mirror_then_disconnect():
    c = WorkbenchController()
    assert c.connect("demo") is True
    assert c.is_connected()
    assert _wait(lambda: "MINITEL WORKBENCH" in c.screen_text())
    assert c.status_line() == "Connected to Local Demo"
    c.disconnect()
    assert not c.is_connected()


def test_status_line_without_hardware():
    c = WorkbenchController()
    assert c.status_line() == "Telephone mode (no cable needed)"


def test_screen_lines_shape():
    c = WorkbenchController()
    lines = c.screen_lines()
    assert len(lines) == c.rows
    assert all(len(line) == c.cols for line in lines)


def test_clear_without_hardware_is_graceful():
    c = WorkbenchController()
    assert c.clear_minitel() == "No Minitel connection to clear."


def test_link_info_without_hardware_is_graceful():
    c = WorkbenchController()
    assert c.link_info().startswith("No Minitel cable connected")


def test_resources_available():
    c = WorkbenchController()
    assert len(c.resources()) >= 6


def test_unknown_service_sets_error():
    c = WorkbenchController()
    assert c.connect("nope") is False
    assert c.state == "error"
