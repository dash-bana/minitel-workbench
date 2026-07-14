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

Minitel Workbench is a toolkit for Minitel owners, whether they connect by
telephone or by USB cable, or don't own a terminal yet. It provides a service
directory, documentation, an offline demo, session recording, a Mac-side mirror
of what the terminal shows, and — for owners with a USB adapter — a direct bridge
to Minitel services such as Retrocampus and MiniPavi.

It began as a debugging session that got a 1984 Radiotechnique Minitel back onto
today's Internet. See [`docs/design/design-notebook.md`](docs/design/design-notebook.md).

## Why it exists

Most working Minitels still dial in by telephone; only a few have the USB
adapter. Existing tools tend to assume the adapter. Workbench does not: it is
usable with no cable, and the adapter adds further tools (live mirror, recording,
diagnostics, benchmark). The design rules it follows — no "recommended" labels,
no lecturing about old hardware, an interface that talks about services rather
than sockets — are set out in [the Constitution](CONSTITUTION.md).

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
| **Retrocampus** | BBS by Francesco Sblendorio — forums, files, games, AI (Mistral, ChatGPT for Patreon supporters). Free to access. | WebSocket · telephone |
| **MiniPavi** | Gateway/directory to hundreds of Minitel services. | Telnet `go.minipavi.fr:516` · telephone |
| **Local Demo** | Pages served from inside Workbench — no network, no service. That makes it the answer to *"is it me, or is it them?"*: if the demo draws correctly on your Minitel, the fault is out on the network, not on your desk. Its **display test** (page 5) states on screen what each line should look like. | in-process |

The directory is data ([`src/minitel_workbench/services/directory.json`](src/minitel_workbench/services/directory.json)),
so adding a service is a one-line contribution rather than a release.

## Status

Tested against a physical Minitel (a 1984 Radiotechnique NFZ 300): the bridge
connected to MiniPavi over the USB serial link, drew pages, and navigated from
both the terminal's keyboard and the Mac's. The display test renders correctly on
the CRT — accents, mosaics, REP run-length fills, inverse and blink — which
exercises the decoder end to end. That terminal answers PRO3 commands but
reports no ROM identity, which is normal for a first-generation Minitel 1.

Working today: direct serial↔TCP bridge with Telnet filtering, WebSocket
transport, auto-reconnect on idle drop, offline demo with a display test,
auto-detect, persistent config, service directory, bidirectional recording, a
CEPT level-2 colour mirror (ANSI + HTML, blink included), a one-click setup
report (cable, driver, line speed, terminal identity, services), a telephone
dialing assistant and service status monitor, a protocol inspector and
`.vdt`/recording viewer, and a resources/museum directory with credits.

Also: a benchmark for the serial link, a local microserver that serves your own
pages to the terminal, a Videotex page builder, and a `clear` command for a
garbled screen. AI is treated as a service you connect to (e.g. Retrocampus)
rather than something Workbench calls with an API key; see the Constitution.

CLI surface: `list · scan · doctor · selftest · demo · clear · status ·
resources · call · view · inspect · serve · benchmark · connect`.

Planned: DRCS + serial-attribute rendering, a visual `.vdt` editor, a richer live
GUI monitor, and a packaged `.app`.

## Contributing

Contributions are welcome. Read the [Constitution](CONSTITUTION.md) and the
[Contributing guide](CONTRIBUTING.md) first.

## License

MIT — see [LICENSE](LICENSE).
