"""Detect the FTDI cable/driver state and guide a new owner through setup.

The single biggest reason cable-buyers give up is the macOS driver install: the
adapter enumerates on USB, but until FTDI's DriverKit extension is installed and
*approved in System Settings*, no ``/dev/cu.usbserial-*`` appears. This module
tells the three states apart and walks the user through the fix, automating the
mechanical parts (copy to /Applications, de-quarantine, launch) that turned the
design notebook's setup into an afternoon.

macOS security means one step can't be automated — the user must click "Allow"
for the system extension (and maybe restart). The wizard gets them to that exact
button and confirms success by polling.
"""

from __future__ import annotations

import glob
import os
import subprocess
from dataclasses import dataclass

FTDI_VCP_URL = "https://ftdichip.com/drivers/vcp-drivers/"

#: Where to get the cable, for someone who hasn't got one. The same seller has
#: had restored Minitels. Listings move — the resources directory carries a
#: fallback ("search eBay.fr for 'câble Minitel USB DIN'").
CABLE_URL = "https://www.ebay.fr/itm/315958961464"
_INSTALLER_NAME = "FTDIUSBSerialVCPDextInstaller.app"

# Setup states
READY = "ready"  # serial port exists — good to go
DRIVER_MISSING = "driver_missing"  # adapter on USB, but no serial port yet
NO_ADAPTER = "no_adapter"  # no FTDI adapter seen at all


def _run(cmd: list[str], timeout: float = 15.0) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        ).stdout
    except Exception:
        return ""


def usb_ftdi_present() -> bool:
    """True if an FTDI adapter is on the USB bus — even with no driver."""
    out = _run(["system_profiler", "SPUSBDataType"])
    low = out.lower()
    return "0x0403" in low or "ft232" in low or "ftdi" in low


def driver_active() -> bool:
    """True if the FTDI DriverKit system extension is activated + enabled."""
    out = _run(["systemextensionsctl", "list"])
    return any(
        "ftdi" in line.lower() and "activated enabled" in line.lower() for line in out.splitlines()
    )


def serial_node_present() -> bool:
    return bool(glob.glob("/dev/cu.usbserial*"))


@dataclass
class SetupState:
    state: str
    usb_present: bool
    driver_active: bool
    serial_node: bool

    @property
    def ready(self) -> bool:
        return self.state == READY


def detect() -> SetupState:
    usb = usb_ftdi_present()
    drv = driver_active()
    node = serial_node_present()
    if node:
        state = READY
    elif usb:
        state = DRIVER_MISSING
    else:
        state = NO_ADAPTER
    return SetupState(state, usb, drv, node)


def find_installer() -> str | None:
    """Look for FTDI's VCP installer where owners usually download it."""
    for base in (
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Desktop"),
        "/Applications",
    ):
        hits = glob.glob(os.path.join(base, "**", _INSTALLER_NAME), recursive=True)
        if hits:
            return hits[0]
    return None


def guidance(state: SetupState, installer: str | None) -> list[str]:
    """Human, actionable steps for the current state (no jargon up front)."""
    if state.state == READY:
        return [
            "Your Minitel connection is ready.",
            "Pick a service and connect — you're all set.",
        ]
    if state.state == NO_ADAPTER:
        return [
            "No USB Minitel adapter detected.",
            "Plug the cable into the Mac and the Minitel's DIN socket —",
            "or, if you connect by telephone, you don't need the cable at all.",
            "",
            "Don't have the cable? It's a USB-to-DIN 5-pin lead:",
            f"     {CABLE_URL}",
            "That seller sometimes has restored Minitels, too.",
        ]
    # DRIVER_MISSING
    steps = [
        "Your adapter is plugged in, but its driver isn't installed yet.",
        "That's the one manual step macOS requires. Here's the whole thing:",
        "",
    ]
    if installer:
        steps.append(f"1. Open the installer already on your Mac:\n     {installer}")
    else:
        steps.append(f"1. Download the FTDI VCP driver:\n     {FTDI_VCP_URL}\n     then open it.")
    steps += [
        "   Click 'Install FTDI USB Serial Dext VCP'.",
        "2. Approve it: System Settings → Privacy & Security → click Allow.",
        "3. Restart if asked, then reconnect the cable.",
        "",
        "Re-check any time with:  minitel setup",
    ]
    return steps


def prepare_installer(installer: str) -> tuple[bool, str]:
    """Copy the installer into /Applications and de-quarantine it, so it runs
    from the required location (avoids the App-Translocation trap from the
    notebook). Uses an admin prompt. Returns (ok, message)."""
    dest = f"/Applications/{_INSTALLER_NAME}"
    script = (
        f'do shell script "ditto {_q(installer)} {_q(dest)} && '
        f'xattr -cr {_q(dest)}" with administrator privileges'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=120)
    except Exception as exc:  # pragma: no cover - needs a real install
        return False, f"Could not copy the installer: {exc}"
    subprocess.run(["open", "-na", dest], check=False)
    return True, f"Launched the installer from {dest}. Click 'Install FTDI USB Serial Dext VCP'."


def open_privacy_settings() -> None:  # pragma: no cover - opens a GUI pane
    subprocess.run(
        ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy"],
        check=False,
    )


def _q(path: str) -> str:
    """Quote a path for an AppleScript 'do shell script' string."""
    return "'" + path.replace("'", "'\\''") + "'"
