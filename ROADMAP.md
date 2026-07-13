# Roadmap

Every release is meant to be usable on its own. Versions are milestones, not
marketing. Status reflects what is actually in the tree.

| Ver | Theme | Status |
|----:|-------|--------|
| 0.1 | Stable direct bridge (serial ⇄ TCP), Telnet filter | ✅ done |
| 0.2 | Auto-detect serial, persistent config, service directory, first-run, CLI | ✅ done |
| 0.3 | WebSocket transport (Retrocampus/`ws` servers), Local Demo service | ✅ done |
| 0.4 | Session recording (bidirectional, timestamped) | ✅ done |
| 0.5 | Mac mirror — text/semigraphics (capability L1) | ✅ done (L1) |
| 0.6 | Tkinter GUI shell + first-run wizard | ✅ done (skeleton) |
| 0.7 | **CEPT renderer** — colour/blink/inverse/underline/conceal/size + ANSI & HTML output (L2) | ✅ done (L2); DRCS + serial-attribute semantics pending |
| 0.8 | Telephone assistant (bilingual dial guide, service status monitor) | ✅ done |
| 0.9 | Studio — `.vdt` viewer (+HTML), page builder, AI page generation | 🚧 viewer + builder done; AI + visual editor pending |
| 0.10 | Museum & Resources (curated external links + credits) | ✅ done |
| 0.11 | Developer — protocol inspector, packet capture, local microserver, live monitor | 🚧 inspector + capture + microserver done; live monitor pending |
| 0.12 | Benchmark suite (throughput + safe multi-speed sweep, recover to 1200 7E1) | ✅ done |
| 1.0 | Polish, docs site, packaged `.app`, community launch | ⏳ planned |

### CEPT status (0.7)

Level 2 is implemented: the decoder interprets the Teletel colour/blink/inverse/
underline/conceal/size attribute escapes onto a per-cell attribute grid, and the
screen renders to ANSI (terminal mirror) and self-contained HTML (screenshots).
Two known gaps remain, both requiring a live terminal to validate and so left as
follow-ups: **DRCS** (downloadable character sets, L3) and **serial/spacing
attribute semantics** (real Minitel colour attributes occupy a cell; we currently
model them as non-spacing pen changes). Neither reduces older-terminal support.

## What "done" means here

The 0.1–0.10 items above are implemented and covered by tests that run with **no
hardware and no network**. The serial bridge and the decoder are additionally
**verified against a physical Minitel** (a 1984 Radiotechnique NFZ 300 on
MiniPavi): pages drew cleanly and keyboard navigation worked. That real session
also drove two decoder fixes — Videotex **REP** (run-length fills) and Minitel
**PRO1/2/3** protocol sequences — plus **auto-reconnect** on idle disconnect.

## Definition of Done (per change, borrowed from the notebook)

- builds / imports cleanly with zero third-party packages
- tests pass (`pytest`)
- lint clean (`ruff`, `black --check`)
- docs updated
- CHANGELOG updated
- no known regression against older Minitels (rule VII)

## Explicit non-goals

- General retro-terminal emulation (VT100/ANSI/Commodore/Amiga).
- Anything that makes the USB adapter a prerequisite for core value.
- "Recommended" transport labels.
