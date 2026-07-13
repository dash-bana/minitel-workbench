"""Find a Minitel USB serial adapter without making the user learn "FTDI".

Detection prefers ``pyserial``'s port enumeration (which exposes USB VID/PID so
we can recognise the FTDI FT232R the community's adapters use), and falls back to
globbing ``/dev/cu.usbserial*`` on macOS when ``pyserial`` isn't installed. Either
way the *user-facing* label never says "FTDI" or "DIN" (Constitution rule I) —
that detail lives in :attr:`DetectedAdapter.advanced`.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass, field

# USB IDs of the adapters the Minitel community uses. Internal detail only.
_FTDI_VID = 0x0403
_KNOWN_USB_SERIAL_VIDS = {
    0x0403,  # FTDI (FT232R and friends)
    0x10C4,  # Silicon Labs CP210x
    0x067B,  # Prolific PL2303
    0x1A86,  # QinHeng CH340/CH341
}


@dataclass
class DetectedAdapter:
    """A candidate connection to a Minitel."""

    device: str  # e.g. /dev/cu.usbserial-A5XK3RJT
    #: What we show the user — deliberately free of "USB/FTDI/DIN" jargon.
    label: str = "Possible Minitel connection"
    likely_minitel: bool = False
    #: Implementation detail, surfaced only under Diagnostics/Advanced.
    advanced: dict[str, str] = field(default_factory=dict)


def _from_pyserial() -> list[DetectedAdapter] | None:
    try:
        from serial.tools import list_ports  # type: ignore
    except Exception:
        return None

    adapters: list[DetectedAdapter] = []
    for port in list_ports.comports():
        # macOS exposes both /dev/cu.* (call-out) and /dev/tty.*; prefer cu.*.
        if port.device.startswith("/dev/tty."):
            continue
        vid = port.vid
        known = vid in _KNOWN_USB_SERIAL_VIDS if vid is not None else False
        advanced = {"device": port.device}
        if port.description:
            advanced["description"] = port.description
        if vid is not None and port.pid is not None:
            advanced["usb_id"] = f"{vid:04x}:{port.pid:04x}"
        if port.serial_number:
            advanced["serial_number"] = port.serial_number
        adapters.append(
            DetectedAdapter(
                device=port.device,
                label="Minitel connection detected" if known else "Serial device detected",
                likely_minitel=known,
                advanced=advanced,
            )
        )
    return adapters


def _from_glob() -> list[DetectedAdapter]:
    adapters: list[DetectedAdapter] = []
    for device in sorted(glob.glob("/dev/cu.usbserial*")):
        adapters.append(
            DetectedAdapter(
                device=device,
                label="Minitel connection detected",
                likely_minitel=True,
                advanced={"device": device, "detected_by": "device-name pattern"},
            )
        )
    return adapters


def find_minitel_adapters() -> list[DetectedAdapter]:
    """Return candidate adapters, most-likely-Minitel first, de-duplicated.

    macOS can expose one physical FTDI adapter under two device nodes — a
    location name (``usbserial-4``) and a serial name (``usbserial-A5XK3RJT``) —
    with the same USB serial number. We collapse those to one entry, preferring
    the stable serial-named node, so the user isn't shown (or auto-connected to)
    the same Minitel twice.

    Never raises and never requires ``pyserial``; an empty list simply means
    "no cable found," which is a perfectly normal (majority) state.
    """
    adapters = _from_pyserial()
    if adapters is None:
        adapters = _from_glob()

    def stable_name(a: DetectedAdapter) -> bool:
        sn = a.advanced.get("serial_number")
        return bool(sn and sn in a.device)

    # Prefer likely-Minitel, then the stable (serial-named) node, then name.
    adapters.sort(key=lambda a: (not a.likely_minitel, not stable_name(a), a.device))

    deduped: list[DetectedAdapter] = []
    seen_serials: set[str] = set()
    for a in adapters:
        sn = a.advanced.get("serial_number")
        if sn:
            if sn in seen_serials:
                continue
            seen_serials.add(sn)
        deduped.append(a)
    return deduped


def best_adapter() -> DetectedAdapter | None:
    """The single most likely Minitel connection, or ``None``.

    Only returns an adapter we actually recognise as a probable Minitel (by USB
    vendor id or a ``usbserial`` device name). Unrelated serial devices — a
    Bluetooth port, a debug console — are never auto-selected for a connection.
    """
    for adapter in find_minitel_adapters():
        if adapter.likely_minitel:
            return adapter
    return None
