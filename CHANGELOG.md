# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [Unreleased]

### Changed / Removed — AI scope + easier relaunch
- **Removed the built-in `minitel ai` page generator** (and `ai.py`). Per the
  Constitution, AI is *a service you connect to* (e.g. Retrocampus's Patreon
  Mistral/ChatGPT), not something Workbench calls with a key. No API keys anywhere.
- `minitel connect` with **no service** now reconnects to your last-used one.
- Double-click launcher `scripts/Minitel Connect.command` — get back online with
  no terminal commands (finds the project, activates the venv, connects).
- Added `minitel clear` to reset a garbled screen (content + status row 0), and
  de-duplicated one adapter that macOS exposes under two device nodes.


### Added — session filmstrip (from real use)
- `minitel view <file> --filmstrip out.html` renders *every* page a session
  displayed, not just the final screen. Found because `view` showed a recording's
  idle screensaver instead of the weather page that had scrolled past.


### Added — AI page generation (0.9) + polish
- `minitel ai "<prompt>"` generates a Videotex page: the model returns a JSON
  page spec, `build_page` encodes it (so output is always valid). Provider order
  is Mistral → ChatGPT → offline template (Constitution: Mistral first). Uses only
  the standard library. `--save`, `--html`, `--provider`.
- `scripts/build_app.sh` (experimental py2app bundle) and a Studio how-to guide.


### Added — page builder + local microserver (0.9/0.11)
- `videotex/page.py`: build valid Videotex from a simple spec (title, coloured
  lines, footer) — a dict-friendly surface so content can be described without
  touching control bytes.
- `MenuServerTransport`: a generic in-process Videotex menu server. Give it named
  pages and the Mac becomes a service your Minitel browses (menu → ENVOI → page →
  SOMMAIRE).
- `minitel serve DIR`: serve a folder of `.vdt` pages to the Minitel, or preview
  the menu with no hardware via `--preview`.


### Added — benchmark suite (0.12)
- `minitel benchmark` measures write throughput at 1200 7E1 (chars/sec, est. page
  time); `--all` sweeps 300/1200/4800/9600 (add `--experimental` for 19200) with
  a human clean/garbled/nothing check per speed, and **always recovers to 1200
  7E1** (recovery is in a `finally`, so even an abort leaves the link safe).


### Hardware-verified + fixes from a real MiniPavi session
- **Verified the serial bridge against a physical Minitel** (Radiotechnique NFZ
  300) connecting to MiniPavi: clean rendering and keyboard navigation.
- Decoder now handles Videotex **REP** (`0x12` run-length repeat) — fills and
  lines that were missing from the mirror now render.
- Decoder and inspector now recognise Minitel **PRO1/2/3** protocol sequences
  (`ESC 0x39/0x3A/0x3B`) instead of mis-printing their parameters as text.
- **Auto-reconnect**: `minitel connect` re-establishes a dropped session
  automatically (default up to 60 min; `--no-reconnect`, `--reconnect-for MIN`),
  so an idle timeout no longer means walking back to the machine. TCP keepalive
  enabled to detect silent drops.
- `minitel inspect --direction` values are now shell-safe (`shown` / `typed`)
  instead of `service->terminal` (the `>` was parsed as a shell redirect).

### Added — Museum & Resources + credits (0.10)
- `minitel resources` — curated external links (Musée du Minitel, Alcatel museum,
  Wikipedia, Le Monde, telematics history) plus community/tool credits, grouped
  and community-first. `--open <id>` opens one in the browser.
- `CREDITS.md` acknowledging Retrocampus/Francesco, MiniPavi, pR-0000's bridge,
  the adapter makers, and the museums — per the "link out and credit" rules.

### Added — protocol inspector + .vdt viewer (0.9/0.11)
- `videotex/protocol.py`: annotates a Videotex byte stream as human events
  ("cursor → row 8 col 19", "foreground red", "KEY ENVOI", grouped text runs) —
  the readable view the notebook wished for during debugging.
- `minitel view <file>`: render a `.vdt` page or `.mtr` recording to the terminal
  (colour) or to a self-contained HTML screenshot (`--html`).
- `minitel inspect <file>`: annotate the bytes of a `.vdt` or one direction of a
  `.mtr` recording.
- `recording.stream_from_recording()`: reconstruct either direction's raw bytes.

### Added — telephone assistant (0.8)
- `minitel call <service>` — bilingual (EN/FR) dial-a-service instructions for
  the majority of owners who connect by phone. No hardware needed.
- `minitel status` — concurrent, dependency-free reachability check of directory
  services (TCP/Telnet/WebSocket host:port probe; demo always online; telephone
  reported as unknown). Makes outbound connections only when run.

### Added — CEPT level-2 renderer (0.7)
- Per-cell attribute grid on the `Screen` (colour, blink, inverse, underline,
  conceal, double-width/height, mosaic) — strictly additive, so monochrome
  terminals render exactly as before.
- Decoder now interprets the Teletel attribute escapes (ESC + code) onto a pen.
- ANSI terminal rendering (`to_ansi`, `framed(color=True)`) and a self-contained
  HTML export (`to_html`) for colour-accurate screenshots — both dependency-free.
- Offline demo gained a COLOURS page exercising the attribute set.
- Known follow-ups (need a live terminal): DRCS (L3) and serial/spacing attribute
  semantics.

### Added — project bootstrap (0.1 → 0.6)
- Project constitution, architecture, roadmap, contributor guide, license (MIT).
- `minitel_workbench` package with a zero-third-party-dependency core.
- **Link** abstraction: `SerialLink` (optional `pyserial`, 1200 7E1 default,
  capability profile) and `LoopbackLink` (in-process, for tests/emulator).
- **Transport** abstraction: `TcpTransport` (+ Telnet IAC negotiation filter),
  `WebSocketTransport` (`ws`/`wss`, optional `websocket-client`), and a fully
  offline `LocalDemoTransport`.
- **Bridge**: proven direct byte-forwarding loop with recorder + monitor taps.
- **Videotex** L1 decoder driving a 24×40 `Screen` model — the text-mode Mac
  mirror (graceful degradation; full CEPT renderer is on the roadmap).
- **Recorder**: bidirectional, timestamped session logging.
- **Services**: curated `directory.json` (Retrocampus featured, MiniPavi gateway,
  Local Demo; Mistral listed before ChatGPT) with a `registry` loader.
- **Config**: persistent JSON settings in the platform config directory.
- **CLI**: `list`, `scan`, `doctor`, `demo`, `connect` — all usable with no
  hardware; jargon kept out of normal output.
- Optional Tkinter GUI shell with a first-run destination picker; degrades to a
  precise install hint when Tk is unavailable.
- Tests covering the Telnet filter, registry, config, decoder, local demo,
  screen model, and a no-hardware end-to-end path. GitHub Actions CI.

### Not yet done
- Verification against a physical Minitel (none attached to the build machine).
- Full CEPT L2/L3 renderer, telephone assistant, Studio, Museum, Developer
  tools, and the all-speeds benchmark (see `ROADMAP.md`).
