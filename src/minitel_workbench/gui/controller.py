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

#: The Minitel function-key row, in the order it appears on the terminal.
FUNCTION_KEYS: tuple[tuple[str, C.Key], ...] = (
    ("Sommaire", C.Key.SOMMAIRE),
    ("Annulation", C.Key.ANNULATION),
    ("Retour", C.Key.RETOUR),
    ("Répétition", C.Key.REPETITION),
    ("Guide", C.Key.GUIDE),
    ("Correction", C.Key.CORRECTION),
    ("Suite", C.Key.SUITE),
    ("Envoi", C.Key.ENVOI),
)


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
        if svc.transport_kind == "demo":
            # Answer "what is this for?" where the question gets asked.
            self.message = (
                "Local Demo — no network: these pages come from Workbench itself. "
                "Type 1 for why this exists, or 5 for the test card."
            )
        else:
            self.message = f"Connected to {svc.name} — type a code and press Envoi."
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
            from ..transport.local_demo import LocalDemoTransport

            # A demo with a terminal attached belongs *on the terminal*. Only
            # fall back to the in-process stand-in when there is no cable —
            # which is what makes the demo work for people who have no Minitel.
            return self._open_link(local_echo=local_echo, required=False), LocalDemoTransport()

        from ..transport import build_transport

        link = self._open_link(local_echo=local_echo, required=True)
        return link, build_transport(svc.access, name=svc.name)

    def _open_link(self, *, local_echo: bool, required: bool):
        """The Minitel end of the bridge: the real cable if one is there."""
        from ..hardware.capability import profile_for_model
        from ..hardware.detect import best_adapter
        from ..hardware.link import LoopbackLink, SerialLink

        adapter = best_adapter()
        if adapter is None:
            if required:
                raise RuntimeError(
                    "No Minitel connection found — connect the cable, or try Local Demo."
                )
            return LoopbackLink()

        link = SerialLink.open(adapter.device, profile_for_model(None))
        if not local_echo:
            link.write(C.LOCAL_ECHO_OFF)
            time.sleep(0.3)
            for _ in range(50):
                if not link.read(256):
                    break
        return link

    def disconnect(self) -> None:
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None
        if self._thread is not None:
            # Wait for the pump thread to notice. A thread still sitting in
            # select() on descriptors we just closed can wake up on *reused*
            # ones and read bytes meant for the next session.
            self._thread.join(timeout=2.0)
            self._thread = None
        if self.state == "connected":
            self.state = "idle"

    def is_connected(self) -> bool:
        return self._bridge is not None and not self._bridge.closed

    def _fail(self, msg: str) -> None:
        self.state = "error"
        self.message = msg

    # -- keyboard ----------------------------------------------------------
    def send_key(self, data: bytes) -> bool:
        """Send keystrokes to the service, as if typed on the Minitel keyboard.

        With the Local Demo the link is a ``LoopbackLink``, so the bytes are fed
        in at the keyboard end and travel the real path (link -> bridge ->
        service), which keeps any recorder tap honest. With a terminal on the
        serial line there is no way to inject into its output, so the bytes go
        straight to the service — the same bytes it would have received had they
        been typed on the Minitel itself.
        """
        if not data or self._bridge is None or self._bridge.closed:
            return False
        feed_key = getattr(self._bridge.link, "feed_key", None)
        target = feed_key if callable(feed_key) else self._bridge.transport.write
        try:
            target(data)
        except Exception:  # noqa: BLE001 - a dead link must not kill the UI
            return False
        return True

    def send_text(self, text: str) -> bool:
        return self.send_key(text.encode("ascii", "ignore"))

    def send_function_key(self, key: C.Key) -> bool:
        return self.send_key(C.function_key_sequence(key))

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

    def self_test(self) -> str:
        """The report card: what is connected, how fast, and what it is.

        Needs the serial port to itself, so an open session is closed first —
        the terminal cannot answer ENQROM while the bridge is pumping bytes at it.
        """
        from ..diagnostics import run

        was_connected = self.is_connected()
        self.disconnect()
        report = run()
        if was_connected:
            report.add("·", "Session", "disconnected to run this test — reconnect when ready")
        return (
            report.text()
            + "\n\nScreen looking wrong? Connect the Local Demo and open page 5, the test"
            "\ncard. It needs no network, so if it draws correctly the fault is out"
            "\nthere, not here — and if it draws wrong, it says which part failed."
        )

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

    def setup_guidance(self) -> str:
        """Detect the cable/driver state and return actionable steps. Slow
        (~1-2s, runs system_profiler), so call it on demand, not every frame."""
        from ..hardware.setup import DRIVER_MISSING, detect, find_installer, guidance

        st = detect()
        installer = find_installer() if st.state == DRIVER_MISSING else None
        return "\n".join(guidance(st, installer))

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
