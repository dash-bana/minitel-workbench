"""The GUI controller, tested with no display and no hardware.

It drives the real bridge to the offline demo, so these exercise the same code
the window will run — only the Tk rendering is left unverified here.
"""

import time

from minitel_workbench.gui.controller import WorkbenchController
from minitel_workbench.videotex import constants as C


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


def test_telephone_guide_serves_phone_users():
    c = WorkbenchController()
    guide = c.telephone_guide()
    assert "Connexion/Fin" in guide  # real dialing instructions, no cable needed
    assert any(ch.isdigit() for ch in guide)  # includes phone numbers


def test_unknown_service_sets_error():
    c = WorkbenchController()
    assert c.connect("nope") is False
    assert c.state == "error"


def _title(c: WorkbenchController) -> str:
    """The demo prints each page's name on the top line — that is how we know
    which page we are on. (The menu lists every page name, so matching against
    the whole screen would pass even if nothing had happened.)"""
    return c.screen_lines()[0].strip()


def test_keys_navigate_the_demo():
    """Typing a code and pressing Envoi opens a page; Sommaire returns home."""
    c = WorkbenchController()
    assert c.connect("demo") is True
    assert _wait(lambda: _title(c) == "MINITEL WORKBENCH")

    c.send_text("3")
    c.send_function_key(C.Key.ENVOI)
    assert _wait(lambda: _title(c) == "A PROPOS")

    c.send_function_key(C.Key.SOMMAIRE)
    assert _wait(lambda: _title(c) == "MINITEL WORKBENCH")
    c.disconnect()


def test_correction_rubs_out_a_typed_digit():
    c = WorkbenchController()
    assert c.connect("demo") is True
    assert _wait(lambda: _title(c) == "MINITEL WORKBENCH")

    c.send_text("9")  # wrong code…
    c.send_function_key(C.Key.CORRECTION)  # …rubbed out
    c.send_text("2")
    c.send_function_key(C.Key.ENVOI)
    assert _wait(lambda: _title(c) == "DEMO SEMIGRAPHIQUE")
    c.disconnect()


def test_keys_are_ignored_when_not_connected():
    c = WorkbenchController()
    assert c.send_text("1") is False
    assert c.send_function_key(C.Key.ENVOI) is False


def test_test_card_is_reachable_and_states_its_expectations():
    """Page 5 is the diagnostic card: it must render, and it must say what the
    user is supposed to see — a card you can't check against is just a picture."""
    c = WorkbenchController()
    assert c.connect("demo") is True
    assert _wait(lambda: _title(c) == "MINITEL WORKBENCH")

    c.send_text("5")
    c.send_function_key(C.Key.ENVOI)
    assert _wait(lambda: _title(c) == "TEST AFFICHAGE")

    screen = c.screen_text()
    for check in ("ACCENTS", "MOSAIQUE", "REPETITION", "INVERSE", "CLIGNOTANT"):
        assert check in screen, f"the card must exercise {check}"
    assert "ÉÈÀÇÔÏ" in screen  # the accents really are decoded, not mangled
    assert screen.count("attendu") >= 4  # every check states its expected result
    assert "-" * 20 in screen  # the REP run-length fill produced 20 identical glyphs
    c.disconnect()
