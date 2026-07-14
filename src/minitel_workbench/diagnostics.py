"""One click, one report card: what is connected, how fast, and what it is.

The pieces were already here — adapter detection, the driver-state check, the
capability profile, throughput arithmetic, the service probe — but a user had to
know which of six commands to run, and had nowhere to put the answers together.
This gathers them into a single report that can be read aloud over the phone or
pasted into a bug report.

Every line is either measured or marked unknown. Nothing here guesses: if the
terminal will not say what it is, the report says so.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from . import status as status_mod
from .videotex import constants as C


@dataclass
class Report:
    lines: list[tuple[str, str, str]] = field(default_factory=list)  # (mark, label, value)

    def add(self, mark: str, label: str, value: str) -> None:
        self.lines.append((mark, label, value))

    def text(self) -> str:
        width = max((len(label) for _, label, _ in self.lines), default=0)
        return "\n".join(f"{mark} {label:<{width}}   {value}" for mark, label, value in self.lines)

    def __str__(self) -> str:
        return self.text()


def _python_and_extras(report: Report) -> None:
    report.add("·", "Python", f"{sys.version.split()[0]}")

    try:
        import serial  # noqa: F401

        report.add("✓", "Serial support", "pyserial installed")
    except ImportError:
        report.add("✗", "Serial support", "pyserial missing — a cable cannot be used")

    try:
        import tkinter  # noqa: F401

        report.add("✓", "Desktop window", "Tk available")
    except ImportError:
        report.add("·", "Desktop window", "Tk not installed (the CLI works without it)")


def _cable(report: Report):
    """Report the cable and driver, returning the adapter (or None)."""
    from .hardware.detect import best_adapter
    from .hardware.setup import SetupState, detect

    adapter = best_adapter()
    state: SetupState = detect()

    if adapter is None:
        report.add("·", "Cable", "none found — telephone mode (no cable needed)")
        if state.usb_present and not state.driver_active:
            report.add("✗", "Driver", "FTDI cable seen, but its driver is not approved")
        return None

    report.add("✓", "Cable", f"{adapter.device}")
    report.add("✓", "Driver", "active" if state.driver_active else "serial port present")
    return adapter


def _link_and_terminal(report: Report, adapter) -> None:
    """Open the link, ask the terminal what it is, and state the line settings."""
    from .benchmark import theoretical_cps
    from .hardware.capability import profile_for_model
    from .hardware.identify import identify
    from .hardware.link import SerialLink

    profile = profile_for_model(None)
    cps = theoretical_cps(profile.default_speed, profile.framing)
    report.add(
        "·",
        "Line",
        f"{profile.default_speed} baud {profile.framing} "
        f"— {cps:.0f} chars/sec, about {1000 / cps:.1f}s for a full page",
    )

    try:
        link = SerialLink.open(adapter.device, profile)
    except Exception as exc:  # noqa: BLE001 - a busy or vanished port must not crash the report
        report.add("✗", "Terminal", f"could not open the port ({exc})")
        return

    try:
        link.write(C.LOCAL_ECHO_OFF)
        identity = identify(link)
    finally:
        link.close()

    if identity is None:
        report.add(
            "·",
            "Terminal",
            "did not identify itself — normal on an early Minitel 1",
        )
        return

    report.add("✓", "Terminal", identity.summary)
    if identity.model is not None:
        m = identity.model
        report.add("·", "Reported by it", f"up to {m.max_speed} baud, keyboard {m.keyboard}")
        report.add(
            "·",
            "Also reports",
            f"80 columns: {'yes' if m.cols80 else 'no'}; "
            f"downloadable characters: {'yes' if m.drcs else 'no'}",
        )
    else:
        report.add("·", "ROM signature", identity.raw.hex(" "))


def _services(report: Report) -> None:
    from .services import load_directory
    from .status import check_all

    for status in check_all(load_directory(), timeout=4.0):
        if status.service_id == "demo":
            continue  # in-process; "reachable" is meaningless
        mark = {status_mod.ONLINE: "✓", status_mod.OFFLINE: "✗"}.get(status.state, "·")
        report.add(mark, status.name, status.detail or status.state)


def run(*, check_services: bool = True) -> Report:
    """Gather the report. Safe with no hardware and no network."""
    report = Report()
    _python_and_extras(report)

    adapter = _cable(report)
    if adapter is not None:
        _link_and_terminal(report, adapter)

    if check_services:
        _services(report)

    return report
