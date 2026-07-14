# Getting started

You do **not** need a Minitel, a cable, or the Internet to try Workbench. Start
there; connect real hardware when you're ready.

## 1. Install

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[serial,ws]"   # extras are optional
```

The `serial` extra is only needed for a real cable; the `ws` extra is needed for
Retrocampus and other `ws://` services. The offline demo needs neither.

## 2. Try it offline

```bash
minitel demo
```

You'll see the Local Demo service drawn on a simulated screen. Type a code from
`1` to `5` and press Enter; `s` returns to the menu; `q` quits. This exercises
the real bridge, a transport, the Videotex decoder, and the screen model — with
no hardware.

If a Minitel *is* connected, the demo runs **on the terminal itself**, and you
can drive it from either keyboard.

## 3. Check your setup

```bash
minitel selftest
```

The report card: your cable and driver, the line speed and what it means in
characters per second, which services are answering, and — if the terminal will
say — what model it is. (`minitel doctor` is the shorter check: Python and
which optional pieces are installed.) A "no cable" result is completely normal;
most Minitels dial in by telephone.

## 4. When the screen looks wrong

Connect the **Local Demo** and open **page 5, the test card**. The demo needs no
network and no service, so if it draws correctly, everything from your cable to
the screen is proven and the fault is out on the network. If it draws wrong, the
fault is local — and the card tells you which part is at fault, because it
prints on the page what each line should look like.

This is the fastest way to answer "is it me, or is it them?" — see
[When the screen looks wrong](diagnosing.md).

## 5. Connect a real Minitel

This is the path proven in the design notebook, on a 1984 Radiotechnique
terminal. Do it on the machine the Minitel is plugged into.

1. Power the Minitel on and leave it showing **F** (local mode). **Do not press
   Connexion/Fin** — that dials the internal phone modem, which isn't what the
   cable connection uses.
2. Find the connection (no jargon needed):
   ```bash
   minitel scan
   ```
3. Connect to a service:
   ```bash
   minitel connect retrocampus     # WebSocket (needs the ws extra)
   minitel connect minipavi        # Telnet go.minipavi.fr:516
   ```
   Add `--record` to save the session, or `--mirror` to print the last screen on
   exit. Press Ctrl-C to disconnect.

   If the service drops your session after a while of inactivity, Workbench
   **reconnects automatically** (for up to 60 minutes) — you don't have to
   re-run anything. Use `--no-reconnect` to turn that off, or
   `--reconnect-for MIN` to change the window.

### The serial settings, for the curious

Workbench opens the port at **1200 baud, 7 data bits, even parity, 1 stop bit
(7E1)**, no flow control — the documented maximum for first-generation Minitels.
You never have to set this; it's the default profile. (If you ever see a
backwards `?` on the screen, that's a parity/framing mismatch — the classic
symptom from the notebook — and it means something reopened the port at 8N1.)

## Troubleshooting

- **`minitel connect` says no connection found** but the terminal is plugged in:
  run `minitel scan --advanced` to see the raw device, and make sure the FTDI
  driver is installed (macOS may need approval under System Settings → Privacy &
  Security the first time).
- **The desktop window won't open**: your Python was built without Tk. The CLI
  works regardless; to get the window, `brew install python-tk`.
- **A service stalls**: disconnect (Ctrl-C) and reconnect. The bridge itself
  doesn't buffer state.
