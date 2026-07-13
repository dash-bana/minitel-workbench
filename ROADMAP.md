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
| 0.7 | **Full CEPT renderer** — color, mosaics, DRCS, double-height (L2/L3) | ⏳ planned |
| 0.8 | Telephone assistant (dial guide, service status monitor) | ⏳ planned |
| 0.9 | Studio — `.vdt` viewer/editor, PNG capture, AI page generation | ⏳ planned |
| 0.10 | Museum & Resources (curated external links, model docs) | ⏳ planned |
| 0.11 | Developer — protocol analyzer/monitor, packet capture, local microserver | ⏳ planned |
| 0.12 | Benchmark suite (all speeds × framings, safe recovery to 1200 7E1) | ⏳ planned |
| 1.0 | Polish, docs site, packaged `.app`, community launch | ⏳ planned |

## What "done" means here

The 0.1–0.6 items above are implemented and covered by tests that run with **no
hardware and no network**. They have not yet been exercised against a physical
Minitel on this machine (none is attached) — that is the one verification step
that still needs a human with the terminal. See `docs/guides/getting-started.md`.

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
