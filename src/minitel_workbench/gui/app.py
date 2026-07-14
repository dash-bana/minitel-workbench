"""The Minitel Workbench window.

A thin Tk view over ``WorkbenchController`` — destination buttons, a live,
*drawn* colour mirror of the terminal (mosaics are painted as 2x3 sub-blocks, so
no font glyphs are needed), and a small toolbar. All logic lives in the
controller; this file only builds widgets, forwards clicks, and paints the canvas
from the controller's screen, so the untested surface is as small as possible.

Only imported when Tk is present (see ``gui/__init__.py``).
"""

from __future__ import annotations

import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk

from ..monitor.canvas_render import cell_draw_ops
from ..videotex import constants as C
from .controller import FUNCTION_KEYS, WorkbenchController

_CELL_W = 15
_CELL_H = 22

_DIAGNOSING_URL = (
    "https://github.com/dash-bana/minitel-workbench/blob/main/docs/guides/diagnosing.md"
)

#: Plain-language headings for the resource kinds, so a link's presence is
#: explained by where it sits.
_KIND_HEADINGS = {
    "hardware": "Get a cable, or a Minitel",
    "community": "Community",
    "museum": "Museums & archives",
    "history": "History",
    "article": "Articles",
    "tool": "Other people's tools — the ones this project stands on",
}

#: Mac keys that stand in for the Minitel function keys they most resemble.
_KEYSYM_TO_FUNCTION = {
    "Return": C.Key.ENVOI,
    "KP_Enter": C.Key.ENVOI,
    "BackSpace": C.Key.CORRECTION,
    "Escape": C.Key.ANNULATION,
    "Home": C.Key.SOMMAIRE,
    "Prior": C.Key.RETOUR,  # page up
    "Next": C.Key.SUITE,  # page down
    "Help": C.Key.GUIDE,
    "F1": C.Key.GUIDE,
}


class WorkbenchApp:
    def __init__(self) -> None:
        self.c = WorkbenchController()
        self.root = tk.Tk()
        self.root.title("Minitel Workbench")
        self._busy = False
        self._last_ops: list[tuple] | None = None
        self._widgets_connected = False
        self._build()
        self._poll()

    # -- layout ------------------------------------------------------------
    def _build(self) -> None:
        ttk.Label(self.root, text="Minitel Workbench", font=("Helvetica", 18, "bold")).pack(
            pady=(14, 2)
        )
        self.status = ttk.Label(self.root, text=self.c.status_line(), foreground="#9aa4c0")
        self.status.pack()

        dest = ttk.LabelFrame(self.root, text="Connect to")
        dest.pack(fill="x", padx=16, pady=(12, 6))
        row = ttk.Frame(dest)
        row.pack(fill="x", padx=8, pady=8)
        for svc in self.c.featured():
            ttk.Button(
                row,
                text=svc.name,
                width=15,
                takefocus=False,
                command=lambda s=svc.id: self._connect(s),
            ).pack(side="left", padx=4, expand=True, fill="x")

        tools = ttk.Frame(self.root)
        tools.pack(fill="x", padx=16, pady=(0, 8))
        # Each button takes an equal share of the width, so the row spans the
        # window like the key row below the screen.
        self.disconnect_btn = ttk.Button(
            tools, text="Disconnect", takefocus=False, command=self._disconnect, state="disabled"
        )
        self.disconnect_btn.pack(side="left", padx=3, expand=True, fill="x")
        for label, action in (
            ("Test my setup", self._self_test),
            ("Screen wrong?", self._diagnosing),
            ("Set up cable", self._setup),
            ("Clear screen", self._clear),
            ("Telephone", self._telephone),
            ("Link info", self._link_info),
            ("What's online", self._status_check),
            ("Resources", self._resources),
        ):
            ttk.Button(tools, text=label, takefocus=False, command=action).pack(
                side="left", padx=3, expand=True, fill="x"
            )

        ttk.Label(self.root, text="Minitel screen (live)").pack(anchor="w", padx=16)
        self.canvas = tk.Canvas(
            self.root,
            width=self.c.cols * _CELL_W,
            height=self.c.rows * _CELL_H,
            background="#000000",
            highlightthickness=1,
            highlightbackground="#2a2a33",
        )
        self.canvas.pack(padx=16, pady=(2, 6))

        keys = ttk.LabelFrame(self.root, text="Minitel keys")
        keys.pack(fill="x", padx=16, pady=(0, 6))
        krow = ttk.Frame(keys)
        krow.pack(fill="x", padx=8, pady=8)
        self.key_buttons = [
            ttk.Button(
                krow,
                text=label,
                width=11,
                takefocus=False,
                state="disabled",
                command=lambda k=key: self._send_function(k),
            )
            for label, key in FUNCTION_KEYS
        ]
        for btn in self.key_buttons:
            btn.pack(side="left", padx=2, expand=True, fill="x")

        self.message = ttk.Label(self.root, text="Leave the Minitel on and showing F.")
        self.message.pack(anchor="w", padx=16, pady=(0, 12))

        # Typing anywhere in the window goes to the service, so there is nothing
        # to click into first. Buttons take no focus, so Return/space can't be
        # swallowed by whichever one was pressed last.
        self.root.bind("<Key>", self._on_key)

    # -- actions -----------------------------------------------------------
    def _connect(self, service_id: str) -> None:
        if self._busy:
            return
        self._busy = True
        self.message.config(text=f"Connecting to {service_id}…")

        def work() -> None:
            self.c.connect(service_id)
            self.root.after(0, self._after_connect)

        threading.Thread(target=work, daemon=True).start()

    def _after_connect(self) -> None:
        self._busy = False
        self.message.config(text=self.c.message)
        self._set_connected_widgets(self.c.is_connected())

    def _disconnect(self) -> None:
        self.c.disconnect()
        self._set_connected_widgets(False)
        self.message.config(text="Disconnected.")

    def _diagnosing(self) -> None:
        """The bisection argument, in the window — with the guide a click away.

        The reasoning is stated here rather than only in the docs: someone whose
        screen is garbled is looking at the app, not at a repository.
        """
        win = tk.Toplevel(self.root)
        win.title("Screen wrong?")
        win.geometry("560x340")
        ttk.Label(
            win,
            text="Is it me, or is it them?",
            font=("Helvetica", 15, "bold"),
        ).pack(pady=(14, 6))
        body = (
            "Select Local Demo, then option 5 + Envoi.\n\n"
            "The demo's pages come from Workbench itself — no network, no service, "
            "nobody else to blame.\n\n"
            "• If the display test draws correctly on your Minitel, everything from "
            "the cable to the screen is proven. The fault is out on the network.\n\n"
            "• If it draws wrong, the fault is here — and the page says what each "
            "line should look like, so you can tell which part failed.\n\n"
            "A photograph of a wrong result is enough to report a bug."
        )
        msg = tk.Message(win, text=body, width=500, justify="left")
        msg.pack(padx=18, anchor="w")
        ttk.Button(
            win,
            text="Open the full guide",
            takefocus=False,
            command=lambda: webbrowser.open(_DIAGNOSING_URL),
        ).pack(pady=12)

    def _self_test(self) -> None:
        self.message.config(text="Testing your setup…")

        def work() -> None:
            text = self.c.self_test()
            self.root.after(
                0,
                lambda: (
                    self._show_text("Your setup", text),
                    self.message.config(text=""),
                    self._set_connected_widgets(self.c.is_connected()),
                ),
            )

        threading.Thread(target=work, daemon=True).start()

    def _setup(self) -> None:
        self.message.config(text="Checking the cable and driver…")

        def work() -> None:
            text = self.c.setup_guidance()
            self.root.after(
                0,
                lambda: (self._show_text("Set up your cable", text), self.message.config(text="")),
            )

        threading.Thread(target=work, daemon=True).start()

    def _clear(self) -> None:
        self.message.config(text=self.c.clear_minitel())

    def _telephone(self) -> None:
        self._show_text("How to dial (no cable needed)", self.c.telephone_guide())

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
        """Links, grouped and explained — a bare button with someone's repo name
        on it tells the reader nothing about why it is there."""
        win = tk.Toplevel(self.root)
        win.title("Resources")
        win.geometry("560x560")
        ttk.Label(
            win, text="Explore Minitel history & community", font=("Helvetica", 14, "bold")
        ).pack(pady=(10, 6))

        # The list is longer than the window, so it scrolls.
        canvas = tk.Canvas(win, highlightthickness=0)
        bar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw", width=520)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        bar.pack(side="right", fill="y", pady=(0, 12))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta, "units"))

        last_kind = None
        for res in self.c.resources():
            if res.kind != last_kind:
                last_kind = res.kind
                ttk.Label(
                    body, text=_KIND_HEADINGS.get(res.kind, res.kind.title()), foreground="#8fa1c7"
                ).pack(anchor="w", pady=(10, 2))
            ttk.Button(
                body,
                text=res.title,
                takefocus=False,
                command=lambda u=res.url: webbrowser.open(u),
            ).pack(fill="x", pady=(2, 0))
            if res.note:
                tk.Message(body, text=res.note, width=500, foreground="#9aa4c0", padx=4).pack(
                    anchor="w", pady=(0, 4)
                )

    # -- keyboard ----------------------------------------------------------
    def _on_key(self, event: tk.Event) -> None:
        if not self.c.is_connected():
            return
        key = _KEYSYM_TO_FUNCTION.get(event.keysym)
        if key is not None:
            self._send_function(key)
            return
        char = event.char
        if len(char) == 1 and " " <= char <= "~":  # printable ASCII only
            self.c.send_text(char)

    def _send_function(self, key: C.Key) -> None:
        if self.c.send_function_key(key):
            self.message.config(text=f"Sent {key.name.title()}.")

    def _show_text(self, title: str, text: str) -> None:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("680x360")  # wide enough that the report's columns line up
        box = tk.Text(win, font=("Menlo", 11), wrap="word")
        box.insert("1.0", text or "(nothing)")
        box.config(state="disabled")
        box.pack(fill="both", expand=True, padx=10, pady=10)

    # -- live update -------------------------------------------------------
    def _render(self) -> None:
        # Half-second phases: the terminal blinks, so the mirror blinks with it.
        blink_on = int(time.monotonic() * 2) % 2 == 0
        ops = cell_draw_ops(self.c.screen(), _CELL_W, _CELL_H, blink_on=blink_on)
        if ops == self._last_ops:
            return  # nothing changed — avoid needless redraw/flicker
        self._last_ops = ops
        cv = self.canvas
        cv.delete("all")
        for op in ops:
            if op[0] == "rect":
                _, x0, y0, x1, y1, fill = op
                cv.create_rectangle(x0, y0, x1, y1, fill=fill, outline=fill)
            else:  # text
                _, cx, cy, ch, fill = op
                cv.create_text(cx, cy, text=ch, fill=fill, font=("Menlo", 13))

    def _poll(self) -> None:
        self.status.config(text=self.c.status_line())
        self._render()
        self._set_connected_widgets(self.c.is_connected())
        # Faster than the eye needs for the mirror, but the blink phase turns
        # every 500ms and a slower poll makes it stutter. Redraws are skipped
        # when nothing changed, so this costs little.
        self.root.after(200, self._poll)

    def _set_connected_widgets(self, connected: bool) -> None:
        """Enable Disconnect and the key row exactly when a session is live."""
        if connected == self._widgets_connected:
            return  # no needless reconfiguration
        self._widgets_connected = connected
        state = "normal" if connected else "disabled"
        self.disconnect_btn.config(state=state)
        for btn in self.key_buttons:
            btn.config(state=state)

    def run(self) -> None:
        try:
            self.root.mainloop()
        finally:
            self.c.disconnect()
