"""Turn a session's byte stream into a page-by-page filmstrip.

`view` renders only the *final* screen, which — after an idle timeout — is often
the service's screensaver, not the page you cared about. Splitting the stream on
FF (full-page redraws) recovers every screen the session displayed, which is what
you actually want when reviewing a recording.
"""

from __future__ import annotations

import html as _html

from ..videotex import constants as C
from ..videotex.decoder import Decoder
from .screen import Screen


def split_frames(stream: bytes) -> list[bytes]:
    """Split a service→terminal stream into full-page chunks on FF (0x0C)."""
    frames: list[bytes] = []
    cur = bytearray()
    for b in stream:
        if b == C.FF and cur:
            frames.append(bytes(cur))
            cur = bytearray([C.FF])
        else:
            cur.append(b)
    if cur:
        frames.append(bytes(cur))
    return frames


def frame_screens(stream: bytes, *, min_chars: int = 8) -> list[Screen]:
    """Decode each frame; keep those with at least ``min_chars`` of content."""
    screens: list[Screen] = []
    for chunk in split_frames(stream):
        d = Decoder()
        d.feed(chunk)
        if len(d.screen.text.strip()) >= min_chars:
            screens.append(d.screen)
    return screens


def build_filmstrip(stream: bytes, *, title: str = "Session filmstrip") -> str:
    """A self-contained HTML page showing every screen of ``stream``."""
    screens = frame_screens(stream)
    style = (
        "@keyframes mtl-blink{50%{opacity:0}}"
        "body{background:#15151b;color:#ccd;font-family:-apple-system,Helvetica,sans-serif;"
        "margin:24px}h1{font-weight:600}.grid{display:flex;flex-wrap:wrap;gap:18px}"
        "figure{margin:0}figcaption{margin-top:6px;font-size:12px;color:#9aa;max-width:380px}"
        "pre.mtl{display:inline-block;padding:10px;background:#000;"
        "font:13px/1.15 'Menlo','DejaVu Sans Mono',monospace;letter-spacing:0}"
    )
    figs = []
    for i, screen in enumerate(screens):
        pre = _extract_pre(screen.to_html())
        caption = " ".join(screen.text.split())[:46]
        figs.append(
            f"<figure>{pre}<figcaption>#{i} — {_html.escape(caption)}</figcaption></figure>"
        )
    return (
        f"<!doctype html><meta charset=utf-8><title>{_html.escape(title)}</title>"
        f"<style>{style}</style>"
        f"<h1>{_html.escape(title)} — {len(screens)} screens</h1>"
        f"<div class=grid>{''.join(figs)}</div>"
    )


def _extract_pre(doc: str) -> str:
    start = doc.find("<pre")
    end = doc.rfind("</pre>")
    return doc[start : end + 6] if start >= 0 and end > start else doc
