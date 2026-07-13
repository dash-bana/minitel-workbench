"""The Minitel Workbench window.

A thin Tk view over ``WorkbenchController`` — destination buttons, a live mirror
of the terminal, and a small toolbar (clear, link info, what's online,
resources). All logic lives in the controller; this file only builds widgets and
forwards clicks, so the untested surface is as small as possible.

Only imported when Tk is present (see ``gui/__init__.py``).
"""

from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from tkinter import ttk

from .controller import WorkbenchController

_BG = "#101014"
_FG = "#d6d6e6"
_ACCENT = "#8fb7ff"


class WorkbenchApp:
    def __init__(self) -> None:
        self.c = WorkbenchController()
        self.root = tk.Tk()
        self.root.title("Minitel Workbench")
        self.root.geometry("620x640")
        self.root.minsize(560, 560)
        self._busy = False
        self._build()
        self._poll()

    # -- layout ------------------------------------------------------------
    def _build(self) -> None:
        ttk.Label(self.root, text="Minitel Workbench", font=("Helvetica", 18, "bold")).pack(
            pady=(14, 2)
        )
        self.status = ttk.Label(self.root, text=self.c.status_line(), foreground="#4a4a55")
        self.status.pack()

        dest = ttk.LabelFrame(self.root, text="Connect to")
        dest.pack(fill="x", padx=16, pady=(12, 6))
        row = ttk.Frame(dest)
        row.pack(fill="x", padx=8, pady=8)
        for svc in self.c.featured():
            ttk.Button(
                row, text=svc.name, width=16, command=lambda s=svc.id: self._connect(s)
            ).pack(side="left", padx=4)
        self.disconnect_btn = ttk.Button(
            row, text="Disconnect", command=self._disconnect, state="disabled"
        )
        self.disconnect_btn.pack(side="right", padx=4)

        tools = ttk.Frame(self.root)
        tools.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Button(tools, text="Clear screen", command=self._clear).pack(side="left", padx=3)
        ttk.Button(tools, text="Link info", command=self._link_info).pack(side="left", padx=3)
        ttk.Button(tools, text="What's online", command=self._status_check).pack(
            side="left", padx=3
        )
        ttk.Button(tools, text="Resources", command=self._resources).pack(side="left", padx=3)

        ttk.Label(self.root, text="Minitel screen (live)").pack(anchor="w", padx=16)
        self.mirror = tk.Text(
            self.root,
            height=self.c.rows,
            width=self.c.cols,
            font=("Menlo", 12),
            background=_BG,
            foreground=_FG,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#2a2a33",
            state="disabled",
            wrap="none",
        )
        self.mirror.pack(padx=16, pady=(2, 6), fill="both", expand=True)

        self.message = ttk.Label(self.root, text="Leave the Minitel on and showing F.")
        self.message.pack(anchor="w", padx=16, pady=(0, 12))

    # -- actions -----------------------------------------------------------
    def _connect(self, service_id: str) -> None:
        if self._busy:
            return
        self._busy = True
        self.message.config(text=f"Connecting to {service_id}…")

        def work() -> None:
            ok = self.c.connect(service_id)
            self.root.after(0, lambda: self._after_connect(ok))

        threading.Thread(target=work, daemon=True).start()

    def _after_connect(self, ok: bool) -> None:
        self._busy = False
        self.message.config(text=self.c.message)
        self.disconnect_btn.config(state="normal" if self.c.is_connected() else "disabled")

    def _disconnect(self) -> None:
        self.c.disconnect()
        self.disconnect_btn.config(state="disabled")
        self.message.config(text="Disconnected.")

    def _clear(self) -> None:
        self.message.config(text=self.c.clear_minitel())

    def _link_info(self) -> None:
        self._show_text("Link info", self.c.link_info())

    def _status_check(self) -> None:
        self.message.config(text="Checking services…")

        def work() -> None:
            rows = self.c.services_status()
            text = "\n".join(f"{name:<14} {state:<8} {detail}" for name, state, detail in rows)
            self.root.after(
                0, lambda: (self._show_text("What's online", text), self.message.config(text=""))
            )

        threading.Thread(target=work, daemon=True).start()

    def _resources(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Resources")
        win.geometry("460x360")
        ttk.Label(
            win, text="Explore Minitel history & community", font=("Helvetica", 14, "bold")
        ).pack(pady=8)
        for res in self.c.resources():
            ttk.Button(win, text=f"{res.title}", command=lambda u=res.url: webbrowser.open(u)).pack(
                fill="x", padx=12, pady=2
            )

    def _show_text(self, title: str, text: str) -> None:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("520x300")
        box = tk.Text(win, font=("Menlo", 11), wrap="word")
        box.insert("1.0", text or "(nothing)")
        box.config(state="disabled")
        box.pack(fill="both", expand=True, padx=10, pady=10)

    # -- live update -------------------------------------------------------
    def _poll(self) -> None:
        self.status.config(text=self.c.status_line())
        lines = self.c.screen_lines()
        self.mirror.config(state="normal")
        self.mirror.delete("1.0", "end")
        self.mirror.insert("1.0", "\n".join(lines))
        self.mirror.config(state="disabled")
        if self.c.is_connected() != (self.disconnect_btn["state"] == "normal"):
            self.disconnect_btn.config(state="normal" if self.c.is_connected() else "disabled")
        self.root.after(300, self._poll)

    def run(self) -> None:
        try:
            self.root.mainloop()
        finally:
            self.c.disconnect()
