"""Measure a Minitel's peripheral serial link.

Two things are measurable from the Mac side alone:

* **write throughput** — how fast bytes actually leave for the terminal at a
  given baud (send a known payload, time it to full drain);
* **does a speed render** — by sending a recognisable pattern and asking the
  person to look at the screen (the terminal doesn't echo in local mode, so
  correctness can only be confirmed by eye).

The design notebook asked for an *all-speeds* sweep so the tool helps every
owner, and for it to be **safe**: it always returns the link to the known-good
**1200 7E1**, whatever happens. That recovery is in a ``finally`` here.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from .videotex import constants as C

# Speeds worth trying, in ascending order. 19200+ is experimental.
STANDARD_SPEEDS = (300, 1200, 4800, 9600)
EXPERIMENTAL_SPEEDS = (19200,)
SAFE_SPEED = 1200
SAFE_FRAMING = "7E1"


@dataclass(frozen=True)
class ThroughputResult:
    baud: int
    framing: str
    bytes_sent: int
    seconds: float

    @property
    def chars_per_sec(self) -> float:
        return self.bytes_sent / self.seconds if self.seconds > 0 else float("inf")

    def est_page_seconds(self, page_bytes: int = 1000) -> float:
        cps = self.chars_per_sec
        return page_bytes / cps if cps and cps != float("inf") else 0.0


@dataclass
class SpeedVerdict:
    baud: int
    framing: str
    throughput: ThroughputResult | None
    rendering: str  # "clean" | "garbled" | "nothing" | "skipped"


def make_throughput_payload(nbytes: int = 2000) -> bytes:
    """A large block of printable text for timing.

    Throughput can only be measured honestly if the payload is much bigger than
    the USB adapter's buffers (an FT232R has a 256-byte TX FIFO, plus OS
    buffering). A small page fits entirely in that buffer, so ``write`` returns
    before a single bit hits the wire — which reports absurd speeds. A few KB
    forces ``write`` to block at the real line rate.
    """
    row = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 4  # printable, no control bytes
    body = (row * (nbytes // len(row) + 1))[:nbytes]
    return bytes([C.FF]) + body


def make_test_payload(label: str) -> bytes:
    """A visible, self-identifying Videotex test page for a given speed."""
    out = bytearray()
    out.append(C.FF)  # clear + home
    out += bytes((C.US, C.POS_OFFSET + 1, C.POS_OFFSET + 2))
    out += f"MINITEL WORKBENCH TEST {label}".encode("ascii")[:38]
    out += bytes((C.US, C.POS_OFFSET + 3, C.POS_OFFSET + 2))
    out += b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    out += bytes((C.US, C.POS_OFFSET + 5, C.POS_OFFSET + 2))
    out += bytes([C.SO]) + bytes([0x7F]) * 36 + bytes([C.SI])  # a solid bar
    out += bytes((C.US, C.POS_OFFSET + 7, C.POS_OFFSET + 2))
    out += b"If this is clean, the speed works."
    return bytes(out)


def measure_write_throughput(
    link: object,
    payload: bytes,
    *,
    baud: int,
    framing: str,
    clock: Callable[[], float] = time.perf_counter,
) -> ThroughputResult:
    """Write ``payload`` through ``link`` and time it to full drain.

    ``link.write`` is expected to block until the bytes have been handed to the
    UART (``SerialLink.write`` flushes), so the elapsed time reflects the real
    line rate.
    """
    start = clock()
    link.write(payload)
    elapsed = clock() - start
    return ThroughputResult(baud=baud, framing=framing, bytes_sent=len(payload), seconds=elapsed)


def run_sweep(
    open_at: Callable[[int, str], object],
    speeds: tuple[int, ...],
    verify: Callable[[int, str], str],
    *,
    framing: str = SAFE_FRAMING,
    clock: Callable[[], float] = time.perf_counter,
) -> list[SpeedVerdict]:
    """Test each speed, then **always** recover to 1200 7E1.

    ``open_at(baud, framing)`` opens a link; ``verify(baud, framing)`` returns
    the human's verdict ("clean"/"garbled"/"nothing"/"skipped"). Recovery runs
    in ``finally`` so an exception mid-sweep still leaves the link safe.
    """
    verdicts: list[SpeedVerdict] = []
    try:
        for baud in speeds:
            link = open_at(baud, framing)
            try:
                payload = make_test_payload(f"{baud} {framing}")
                result = measure_write_throughput(
                    link, payload, baud=baud, framing=framing, clock=clock
                )
                rendering = verify(baud, framing)
            finally:
                _safe_close(link)
            verdicts.append(SpeedVerdict(baud, framing, result, rendering))
    finally:
        # Return the link to the known-good state no matter what happened.
        _safe_close(open_at(SAFE_SPEED, SAFE_FRAMING))
    return verdicts


def _safe_close(link: object) -> None:
    close = getattr(link, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass
