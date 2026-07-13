# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [Unreleased]

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
