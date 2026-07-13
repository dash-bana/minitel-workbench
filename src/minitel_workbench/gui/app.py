"""A minimal Tkinter shell: first-run destination picker + live text mirror.

This is a *skeleton* (roadmap 0.6). It honours the Constitution: the first choice
is a destination, never a transport; no method is labelled "recommended"; and it
degrades to a text mirror rather than pretending to be a CEPT renderer. The full
window (Services / Library / Studio / Museum / …) is future work.

Only imported when Tk is present; see ``gui/__init__.py``.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from ..bridge import Bridge
from ..config import Settings
from ..hardware.capability import profile_for_model
from ..hardware.detect import best_adapter
from ..services import load_directory
from ..videotex.decoder import Decoder


class WorkbenchApp:
    def __init__(self) -> None:
        self.settings = Settings.load()
        self.directory = load_directory()
        self.root = tk.Tk()
        self.root.title("Minitel Workbench")
        self.root.geometry("560x520")
        self._bridge: Bridge | None = None
        self._thread: threading.Thread | None = None
        self._decoder = Decoder()
        self._build()

    def _build(self) -> None:
        header = ttk.Label(
            self.root, text="Where would you like to go?", font=("Helvetica", 16, "bold")
        )
        header.pack(pady=(16, 8))

        picker = ttk.Frame(self.root)
        picker.pack(fill="x", padx=16)
        for svc in self.directory.featured():
            row = ttk.Frame(picker)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=svc.name, width=16, font=("Helvetica", 13)).pack(side="left")
            ttk.Label(row, text=svc.description, wraplength=320).pack(side="left", expand=True)
            ttk.Button(row, text="Connect", command=lambda s=svc: self._connect(s.id)).pack(
                side="right"
            )

        self.status = ttk.Label(self.root, text=self._status_text())
        self.status.pack(pady=8)

        self.mirror = tk.Text(
            self.root,
            height=24,
            width=40,
            font=("Menlo", 11),
            background="#101014",
            foreground="#d0d0e0",
            borderwidth=0,
        )
        self.mirror.pack(padx=16, pady=(0, 16), fill="both", expand=True)
        self._render_mirror()

    def _status_text(self) -> str:
        return "Minitel detected" if best_adapter() else "Telephone mode (no cable needed)"

    def _connect(self, service_id: str) -> None:
        svc = self.directory.get(service_id)
        if svc is None:
            return
        self._teardown()

        if svc.transport_kind == "demo":
            from ..hardware.link import LoopbackLink
            from ..transport.local_demo import LocalDemoTransport

            link: object = LoopbackLink()
            transport: object = LocalDemoTransport()
        else:
            adapter = best_adapter()
            if adapter is None:
                self.status.config(text="No Minitel connection — try Local Demo.")
                return
            from ..hardware.link import SerialLink
            from ..transport import build_transport

            try:
                link = SerialLink.open(adapter.device, profile_for_model(None))
                transport = build_transport(svc.access, name=svc.name)
            except (RuntimeError, Exception) as exc:  # noqa: BLE001
                self.status.config(text=str(exc).splitlines()[0])
                return

        self._decoder = Decoder()
        self._bridge = Bridge(link, transport, monitor=self._decoder)
        self.settings.default_service = svc.id
        self.settings.save()
        self.status.config(text=f"Connected to {svc.name}")
        self._thread = threading.Thread(target=self._bridge.run, daemon=True)
        self._thread.start()
        self._poll()

    def _poll(self) -> None:
        if self._bridge and not self._bridge.closed:
            self._render_mirror()
            self.root.after(200, self._poll)

    def _render_mirror(self) -> None:
        self.mirror.delete("1.0", "end")
        self.mirror.insert("1.0", self._decoder.screen.text)

    def _teardown(self) -> None:
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None

    def run(self) -> None:
        try:
            self.root.mainloop()
        finally:
            self._teardown()
