"""The GUI's brain — all logic, no Tk.

Keeping every decision here (and nothing in the Tk view but wiring) means the app
is testable with no display: the controller drives the real bridge, so a headless
test can "connect" to the Local Demo and watch the mirror update. The Tk layer in
``app.py`` only renders what the controller exposes and forwards button clicks.
"""

from __future__ import annotations

import threading
import time

from ..bridge import Bridge
from ..config import Settings
from ..monitor.screen import COLS, ROWS
from ..services import load_directory
from ..videotex import constants as C
from ..videotex.decoder import Decoder


class WorkbenchController:
    def __init__(self) -> None:
        self.directory = load_directory()
        self.settings = Settings.load()
        self.decoder = Decoder()
        self._bridge: Bridge | None = None
        self._thread: threading.Thread | None = None
        self.state = "idle"  # idle | connected | error
        self.current_service: str | None = None
        self.message = ""

    # -- status ------------------------------------------------------------
    def minitel_present(self) -> bool:
        from ..hardware.detect import best_adapter

        return best_adapter() is not None

    def status_line(self) -> str:
        """What the user *has* — never jargon (Constitution rule I)."""
        if self.is_connected():
            return f"Connected to {self.current_service}"
        return "Minitel detected" if self.minitel_present() else "Telephone mode (no cable needed)"

    def featured(self):
        return self.directory.featured()

    # -- connection --------------------------------------------------------
    def connect(self, service_id: str, *, local_echo: bool = False) -> bool:
        svc = self.directory.get(service_id)
        if svc is None:
            self._fail(f"Unknown service: {service_id}")
            return False

        self.disconnect()
        self.decoder = Decoder()

        try:
            link, transport = self._open(svc, local_echo=local_echo)
        except Exception as exc:  # noqa: BLE001 - surface any setup failure to the UI
            self._fail(str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__)
            return False

        self._bridge = Bridge(link, transport, monitor=self.decoder)
        self.current_service = svc.name
        self.state = "connected"
        self.message = f"Connected to {svc.name}"
        self.settings.default_service = svc.id
        try:
            self.settings.save()
        except OSError:
            pass
        self._thread = threading.Thread(target=self._bridge.run, daemon=True)
        self._thread.start()
        return True

    def _open(self, svc, *, local_echo: bool):
        if svc.transport_kind == "demo":
            from ..hardware.link import LoopbackLink
            from ..transport.local_demo import LocalDemoTransport

            return LoopbackLink(), LocalDemoTransport()

        from ..hardware.capability import profile_for_model
        from ..hardware.detect import best_adapter
        from ..hardware.link import SerialLink
        from ..transport import build_transport

        adapter = best_adapter()
        if adapter is None:
            raise RuntimeError(
                "No Minitel connection found — connect the cable, or try Local Demo."
            )
        link = SerialLink.open(adapter.device, profile_for_model(None))
        if not local_echo:
            link.write(C.LOCAL_ECHO_OFF)
            time.sleep(0.3)
            for _ in range(50):
                if not link.read(256):
                    break
        transport = build_transport(svc.access, name=svc.name)
        return link, transport

    def disconnect(self) -> None:
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None
        if self.state == "connected":
            self.state = "idle"

    def is_connected(self) -> bool:
        return self._bridge is not None and not self._bridge.closed

    def _fail(self, msg: str) -> None:
        self.state = "error"
        self.message = msg

    # -- the mirror --------------------------------------------------------
    def screen_lines(self) -> list[str]:
        return [self.decoder.screen.line(r) for r in range(ROWS)]

    def screen_text(self) -> str:
        return self.decoder.screen.text

    def screen(self):
        """The live Screen model, for a graphical renderer."""
        return self.decoder.screen

    # -- actions -----------------------------------------------------------
    def clear_minitel(self) -> str:
        seq = bytes(
            [
                C.ESC,
                0x4C,
                C.SI,
                C.FF,
                C.US,
                0x40,
                0x41,
                C.CAN,
                C.US,
                C.POS_OFFSET + 1,
                C.POS_OFFSET + 1,
            ]
        )
        if self.is_connected():
            try:
                self._bridge.link.write(seq)  # type: ignore[union-attr]
            except Exception:
                pass
            self.decoder.screen.clear()
            return "Cleared the Minitel screen."
        from ..hardware.capability import profile_for_model
        from ..hardware.detect import best_adapter
        from ..hardware.link import SerialLink

        adapter = best_adapter()
        if adapter is None:
            return "No Minitel connection to clear."
        link = SerialLink.open(adapter.device, profile_for_model(None))
        link.write(seq)
        time.sleep(0.3)
        link.close()
        return "Cleared the Minitel screen."

    def link_info(self) -> str:
        from ..benchmark import theoretical_cps
        from ..hardware.capability import profile_for_model
        from ..hardware.detect import best_adapter

        if best_adapter() is None:
            return "No Minitel cable connected — telephone users don't need one."
        prof = profile_for_model(None)
        cps = theoretical_cps(prof.default_speed, prof.framing)
        lines = [
            "Minitel connection detected.",
            f"Serial link: {prof.default_speed} baud, {prof.framing}.",
            f"Throughput: {cps:.0f} chars/sec (~{1000 / cps:.1f}s per full page).",
            "Full speed sweep (watch the screen): run 'minitel benchmark --all'.",
        ]
        return "\n".join(lines)

    def services_status(self, timeout: float = 4.0) -> list[tuple[str, str, str]]:
        from ..status import check_all

        return [(s.name, s.state, s.detail) for s in check_all(self.directory, timeout=timeout)]

    def resources(self):
        from ..resources import load_resources

        return load_resources()

    def telephone_guide(self) -> str:
        """Dialing instructions for services reachable by phone — the primary
        audience's path, needing no cable (Constitution rule II)."""
        from ..telephone import dialing_instructions

        parts = [
            dialing_instructions(svc) for svc in self.directory.all() if svc.telephone_numbers()
        ]
        return "\n".join(parts) if parts else "No telephone numbers listed yet."

    # dimensions, so the view doesn't import the model directly
    rows = ROWS
    cols = COLS
