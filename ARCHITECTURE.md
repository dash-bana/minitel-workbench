# Architecture

Minitel Workbench is a small, layered Python application. The layering exists to
honor two constitution rules in particular: **the telephone user is primary**
(so nothing core may hard-depend on serial hardware) and **transport is hidden
from users** (so the UI talks to abstractions, never to sockets or ports).

```
                 ┌──────────────────────────────────────────┐
   UI / CLI ─────▶            Session / Bridge               │
                 │  pumps bytes  Link ⇄ Transport            │
                 │  taps: Recorder, Monitor(screen decoder)  │
                 └───────┬───────────────────────┬───────────┘
                         │                       │
              ┌──────────▼─────────┐   ┌─────────▼──────────────┐
   Minitel ◀──┤  Link (device side)│   │ Transport (service side)│──▶ Internet
              │  SerialLink        │   │  TcpTransport (+telnet) │
              │  LoopbackLink      │   │  WebSocketTransport     │
              └────────────────────┘   │  LocalDemoTransport     │
                                       └─────────────────────────┘
```

## The two abstractions

Both sides are **selectable byte pipes** — each exposes `fileno()`, `read()`,
`write()`, `close()` — so the bridge can drive them with a single `select()`
loop and stay transport-agnostic.

### `Link` — the terminal side (`hardware/`)
- `SerialLink` — a real Minitel over USB serial via `pyserial`. Opens 1200 7E1
  by default and carries a `CapabilityProfile`. **`pyserial` is an optional
  dependency**; importing the package never requires it. Absence of the library
  or of a device degrades to "no serial link available," never a crash.
- `LoopbackLink` — an in-process `os.pipe` pair used by tests and by the future
  emulator to inject keystrokes and observe output with no hardware.

### `Transport` — the service side (`transport/`)
- `TcpTransport` — raw TCP, with an optional Telnet-negotiation filter (the
  IAC/DO/DONT/WILL/WONT stripper proven in the design notebook). Covers
  MiniPavi (`go.minipavi.fr:516`) and generic telnet/videotex hosts.
- `WebSocketTransport` — `ws://` and `wss://`. Runs the socket in a worker
  thread and exposes an `os.pipe` read-end so it remains `select()`-able like
  everything else. Covers Retrocampus and the `ws`-only community servers.
  Depends on `websocket-client` (optional; clear error only if actually used).
- `LocalDemoTransport` — a fully offline in-process Videotex micro-service. No
  network, no hardware. This is what makes rule II demonstrable.

## The bridge (`bridge.py`)

`Bridge(link, transport, recorder=None, monitor=None)` runs the proven
direct-forwarding loop: bytes from the terminal go straight to the service and
vice-versa, with no GUI event loop in the hot path (that indirection was the
original latency bug). Each direction is optionally *tapped*:
- the `Recorder` writes a timestamped, bidirectional session log;
- the `Monitor` feeds service→terminal bytes through the Videotex decoder into a
  24×40 `Screen` model — this is the "Mac mirror," in text form today and a full
  CEPT renderer later (rule VII: capability levels).

## Videotex / monitor (`videotex/`, `monitor/`)

`videotex/constants.py` names the control bytes (ENVOI, cursor moves, SS2/SO/SI,
etc.). `videotex/decoder.py` is a minimal, capability-L1 interpreter that drives
a `Screen` (cursor positioning, clear/home, printable text, basic semigraphics).
It is deliberately incomplete and honest about it — a full CEPT Level-2/DRCS
renderer is the headline item on the roadmap, and it will *extend* this, never
replace the L1 fallback.

## Services (`services/`)

`registry.py` loads `directory.json`: a curated, refreshable list of
destinations with metadata (description, transport, host/port or URL, telephone
number, website, AI services, language, tags). Featured order and AI ordering
follow the constitution (Retrocampus first; Mistral before ChatGPT). The
directory is data, not code, so the community can add a service without a
release — and a future "Refresh directory" can pull an updated file.

## Config (`config.py`)

Persistent JSON settings under the platform config dir (macOS:
`~/Library/Application Support/Minitel Workbench/`). Stores the chosen default
service, last-used serial device, first-run completion, and per-model capability
profiles. The original GUI bridge lost settings on every launch; persistence is
a requirement here.

## CLI (`cli.py`) and GUI (`gui/`)

`cli.py` is the always-available surface: `list`, `scan`, `connect`, `demo`,
`doctor`. The Tkinter `gui/app.py` is optional and guarded — if Tk is missing
(as on stock Homebrew Python 3.14, per the notebook) the CLI still works and the
GUI prints a precise install hint instead of a traceback.

## Dependency policy

- **Standard library first.** The core imports cleanly with zero third-party
  packages.
- `pyserial`, `websocket-client`, and Tk are **optional**. Each is imported
  lazily at the point of use, and its absence produces a specific, actionable
  message — never an import error at startup.
- Target Python **3.11+**.

## Testability

Because both sides of the bridge are selectable pipes, the whole data path is
exercisable with **no hardware and no network**: `LoopbackLink` +
`LocalDemoTransport` + `Bridge` + decoder + `Screen`. That end-to-end path is a
test (`tests/test_end_to_end.py`) and the thing to run when verifying a change.
