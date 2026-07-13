"""A generic in-process Videotex menu server — the local microserver.

Give it a set of named pages (raw Videotex bytes) and it presents a numbered
menu, serves the chosen page on ENVOI, and returns to the menu on SOMMAIRE. It is
a ``Transport`` like any other, so the bridge connects a real Minitel to it with
no code changes — the Mac becomes the service.

``LocalDemoTransport`` predates this and stays as-is; this is the reusable engine
behind ``minitel serve`` and the AI generator's ``--serve``.
"""

from __future__ import annotations

import os

from ..channel import ByteChannel, ChannelClosed
from ..videotex import constants as C
from ..videotex.page import Line, PageSpec, build_page


class MenuServerTransport(ByteChannel):
    """Serve a menu of pages to a connected terminal."""

    def __init__(self, pages: list[tuple[str, bytes]], *, title: str = "MINITEL WORKBENCH") -> None:
        """``pages`` is an ordered list of (name, videotex_bytes). The menu
        assigns codes 1..N automatically."""
        self.name = title
        self._pages = {str(i + 1): page for i, (_, page) in enumerate(pages)}
        self._menu = self._build_menu(title, [name for name, _ in pages])
        self._tx_r, self._tx_w = os.pipe()
        os.set_blocking(self._tx_r, False)
        self._closed = False
        self._input = bytearray()
        self._expect_key = False
        self._send(self._menu)

    @staticmethod
    def _build_menu(title: str, names: list[str]) -> bytes:
        lines = [Line(f"{i + 1} . {name[:32]}") for i, name in enumerate(names[:16])]
        spec = PageSpec(title=title, lines=lines, footer="CODE + ENVOI")
        return build_page(spec)

    # -- outgoing ----------------------------------------------------------
    def _send(self, data: bytes) -> None:
        if not self._closed:
            os.write(self._tx_w, data)

    def fileno(self) -> int:
        return self._tx_r

    def read(self, size: int = 4096) -> bytes:
        try:
            data = os.read(self._tx_r, size)
        except BlockingIOError:
            return b""
        if data == b"" and self._closed:
            raise ChannelClosed
        return data

    # -- incoming ----------------------------------------------------------
    def write(self, data: bytes) -> None:
        for byte in data:
            if self._expect_key:
                self._expect_key = False
                self._handle_key(byte)
            elif byte == C.SEP:
                self._expect_key = True
            elif 0x20 <= byte <= 0x7E:
                self._input.append(byte)
                self._send(bytes((byte,)))  # echo

    def _handle_key(self, code: int) -> None:
        if code == C.Key.ENVOI:
            choice = self._input.decode("ascii", "ignore").strip()
            self._input.clear()
            self._send(self._pages.get(choice, self._menu))
        elif code == C.Key.SOMMAIRE:
            self._input.clear()
            self._send(self._menu)
        elif code == C.Key.CORRECTION and self._input:
            self._input.pop()
            self._send(bytes((C.BS, 0x20, C.BS)))
        elif code == C.Key.ANNULATION:
            self._input.clear()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for fd in (self._tx_r, self._tx_w):
            try:
                os.close(fd)
            except OSError:
                pass


def load_pages_from_dir(path: str) -> list[tuple[str, bytes]]:
    """Load ``*.vdt`` files from a directory as (name, bytes), sorted by name."""
    import glob
    import os.path

    pages: list[tuple[str, bytes]] = []
    for f in sorted(glob.glob(os.path.join(path, "*.vdt"))):
        with open(f, "rb") as fh:
            pages.append((os.path.splitext(os.path.basename(f))[0], fh.read()))
    return pages
