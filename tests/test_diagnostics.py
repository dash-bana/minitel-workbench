"""The report card, and the terminal identification behind it.

Identification is tested against a fake link that replies exactly as the ROM
does — the real answer can only come from hardware, so what is checked here is
that a correct reply is decoded, a *wrong* one is refused, and silence is
reported as silence rather than invented.
"""

from minitel_workbench import diagnostics
from minitel_workbench.hardware import identify


class FakeLink:
    """Answers ENQROM with whatever bytes the test hands it."""

    def __init__(self, reply: bytes = b"") -> None:
        self.reply = bytearray(reply)
        self.written = bytearray()

    def write(self, data: bytes) -> None:
        self.written.extend(data)

    def read(self, size: int = 4096) -> bytes:
        chunk = bytes(self.reply[:size])
        del self.reply[:size]
        return chunk


def test_identify_decodes_a_known_terminal():
    # SOH 'B' 'v' '4' EOT — the RTIC code with model 'v', which PyMinitel
    # corrects to Philips.
    link = FakeLink(bytes([0x01]) + b"Bv4" + bytes([0x04]))
    ident = identify.identify(link, timeout=0.5)

    assert link.written == identify.ENQROM_QUERY
    assert ident is not None
    assert ident.constructor == "Philips"  # the documented correction, not "RTIC"
    assert ident.model is not None and ident.model.name == "Minitel 2"
    assert ident.version == "4"
    assert "Minitel 2" in ident.summary


def test_identify_reports_an_unknown_code_as_unknown():
    link = FakeLink(bytes([0x01]) + b"Z?1" + bytes([0x04]))
    ident = identify.identify(link, timeout=0.5)

    assert ident is not None
    assert ident.constructor is None  # never guess a maker
    assert ident.model is None
    assert "unknown" in ident.summary
    assert ident.raw.hex(" ") == "01 5a 3f 31 04"


def test_identify_returns_none_when_the_terminal_says_nothing():
    # An early Minitel 1 may simply not answer. That is not an error.
    assert identify.identify(FakeLink(b""), timeout=0.2) is None


def test_identify_refuses_a_malformed_reply():
    assert identify.identify(FakeLink(b"garbage"), timeout=0.2) is None


def test_report_runs_with_no_hardware_and_no_network():
    report = diagnostics.run(check_services=False)
    text = report.text()

    assert "Python" in text
    assert "Cable" in text  # says what it found, or that it found nothing
    assert text == str(report)
