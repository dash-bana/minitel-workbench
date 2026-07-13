# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [Unreleased]

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
