"""Bidirectional, timestamped session recording.

Recordings capture both directions of a session so it can be studied or replayed
later (a preservation goal from the notebook). The format is a simple JSON-lines
log: one event per line, each with a monotonic offset, a direction, and the raw
bytes (hex). It is intentionally trivial to parse and diff.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


class Recorder:
    """Append-only recorder writing JSON-lines to a ``.mtr`` file."""

    def __init__(self, path: str | Path, *, service: str = "", clock: object = time.monotonic):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._t0 = clock()
        self._fh = self.path.open("w", encoding="utf-8")
        self._write({"type": "meta", "service": service, "started": time.time()})

    def _write(self, obj: dict) -> None:
        self._fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self._fh.flush()

    def _event(self, direction: str, data: bytes) -> None:
        self._write(
            {
                "type": "data",
                "t": round(self._clock() - self._t0, 4),
                "dir": direction,
                "hex": data.hex(),
            }
        )

    def from_terminal(self, data: bytes) -> None:
        """Bytes the Minitel keyboard sent toward the service."""
        self._event("terminal->service", data)

    def from_service(self, data: bytes) -> None:
        """Bytes the service sent toward the Minitel display."""
        self._event("service->terminal", data)

    def close(self) -> None:
        if not self._fh.closed:
            self._write({"type": "meta", "ended": time.time()})
            self._fh.close()


def read_recording(path: str | Path) -> list[dict]:
    """Load a recording back into a list of event dicts."""
    events = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events
