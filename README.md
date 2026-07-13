<h1 align="center">Minitel Workbench</h1>

<p align="center"><em>An open-source toolkit for preserving and extending the Minitel ecosystem.</em></p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="CONSTITUTION.md">Constitution</a> ·
  <a href="ARCHITECTURE.md">Architecture</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="docs/guides/getting-started.md">Getting started</a>
</p>

---

Minitel Workbench is everything a Minitel owner needs in one place — **whether
they connect by telephone or by a USB cable, or don't own a terminal yet.** It's
the front door to the surviving Minitel community: a live service directory,
documentation, a fully offline demo, session recording, a Mac-side mirror of
what the terminal shows, and (for owners with a USB adapter) a rock-solid direct
bridge to modern Minitel services like **Retrocampus** and **MiniPavi**.

It began as a debugging session that got a 1984 Radiotechnique Minitel back onto
today's Internet, and turned into a design for the toolkit the community never
quite had. See [`docs/design/design-notebook.md`](docs/design/design-notebook.md).

## Why it exists

Most living Minitels still dial in by telephone; only a handful have the USB
adapter. Existing tools optimize for the rare case. Workbench flips that: it is
**fully useful with no cable**, and the USB adapter simply *unlocks* extra tools
(live mirror, recording, diagnostics, benchmark). Nothing is labelled
"recommended," nothing lectures you about old hardware, and the interface talks
about *services*, not sockets. Those aren't accidents — they're
[the Constitution](CONSTITUTION.md).

## Quick start

Requires **Python 3.11+**. No third-party packages are needed for the offline
demo — the core runs on the standard library alone.

```bash
git clone <your-fork-url> minitel-workbench
cd minitel-workbench

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[serial,ws]"   # extras are optional

# See what's available and check your setup (works with no hardware):
minitel list
minitel doctor

# Try the whole stack offline — no Minitel, no Internet:
minitel demo
```

If you have the USB adapter and a Minitel powered on at **F** (local mode):

```bash
minitel scan                       # find the serial device (no jargon)
minitel connect retrocampus        # or: minitel connect minipavi
```

There is no need to press **Connexion/Fin** on the terminal — leave it at `F`.
Full walkthrough: [`docs/guides/getting-started.md`](docs/guides/getting-started.md).

## Featured destinations

| Service | What it is | Access |
|---------|------------|--------|
| ⭐ **Retrocampus** | Modern BBS by Francesco Sblendorio — forums, files, games, AI (Mistral, ChatGPT for Patreon supporters). Free to access. | WebSocket · telephone |
| ⭐ **MiniPavi** | Gateway/directory to hundreds of Minitel services. | Telnet `go.minipavi.fr:516` · telephone |
| ⭐ **Local Demo** | Offline demo service. Proves keyboard, display, and rendering with no hardware or network. | in-process |

The directory is data ([`src/minitel_workbench/services/directory.json`](src/minitel_workbench/services/directory.json)) —
adding a service is a one-line contribution, not a release.

## Status

**Verified against a physical Minitel** (a 1984 Radiotechnique NFZ 300): the
bridge connected to MiniPavi over the USB serial link, drew pages cleanly, and
navigated by keyboard. Real MiniPavi output also drove the decoder to handle
Videotex **REP** run-length fills and Minitel **PRO** protocol sequences.

Working today: direct serial↔TCP bridge with Telnet filtering, WebSocket
transport, **auto-reconnect** on idle drop, offline demo, auto-detect, persistent
config, service directory, bidirectional recording, a **CEPT level-2 colour
mirror** (ANSI + HTML), a **telephone dialing assistant** and **service status
monitor**, a **protocol inspector** and **`.vdt`/recording viewer**, and a curated
**resources/museum** directory with credits.

Also: a **benchmark** for the serial link, a **local microserver** that serves
your own pages to the terminal, a Videotex **page builder**, and a one-line
**`clear`** for a garbled screen. (AI is deliberately *a service you connect to* —
e.g. Retrocampus — not something Workbench calls with a key; see the Constitution.)

CLI surface: `list · scan · doctor · demo · clear · status · resources · call ·
view · inspect · serve · benchmark · connect`.

Planned: DRCS + serial-attribute rendering, a visual `.vdt` editor, a richer live
GUI monitor, and a packaged `.app`.

## Contributing

This is a **community project**, not one person's. Read the
[Constitution](CONSTITUTION.md) and [Contributing guide](CONTRIBUTING.md). The
Minitel community — Retrocampus, MiniPavi, the Musée du Minitel, the people who
make the adapters — are exactly who this is for.

## License

MIT — see [LICENSE](LICENSE).
