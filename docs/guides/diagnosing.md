# When the screen looks wrong

## Is it me, or is it them?

A Minitel session has a lot of links in the chain: the driver, the cable, the
serial port, the line settings (1200 baud, 7E1), the Videotex decoder, the
service at the far end, and the Internet in between. When a page arrives
garbled — or doesn't arrive — every layer can plausibly blame the next, and you
have no way to tell which one is lying.

The **Local Demo** exists to end that argument. It is the one service with no
network, no telephone, and no third party: the pages come from inside Workbench
itself. So it answers the only question worth asking first.

> **If the demo draws correctly on your Minitel, everything from the cable to
> the glass is proven.** Whatever is wrong is out on the network, or at the
> service — not on your desk.
>
> **If the demo draws wrong, the fault is local**, and it is now narrowed to a
> handful of causes that have nothing to do with any service.

That is what the demo is *for*. Trying it is not a formality; it is the
bisection step that makes everything after it cheap.

## The two tools

### 1. The report card — `minitel selftest`

Or the **Test my setup** button in the window.

```
· Python           3.14.6
✓ Serial support   pyserial installed
✓ Cable            /dev/cu.usbserial-A5XK3RJT
✓ Driver           active
· Line             1200 baud 7E1 — 120 chars/sec (8s a page)
· Terminal         connected; reports no model (normal on a Minitel 1)
✓ MiniPavi         go.minipavi.fr:516 reachable
```

It tells you, in one place, what is actually connected and what is answering.
Two lines are worth understanding:

- **Line** — 1200 baud is not slow by mistake; it is the documented maximum for
  a first-generation Minitel. 120 characters per second means a full 40×24 page
  takes about eight seconds to paint. **A page that fills in visibly, from the
  top, is not a bug.** It is what 1982 looked like.
- **Terminal** — Workbench asks the terminal to identify itself (the ROM
  signature). Later models answer with a make and model. An early Minitel 1 says
  nothing at all, and that is normal, not a fault. Workbench will never guess a
  model it wasn't told.

### 2. The test card — the demo's page 5

Connect to **Local Demo**, type `5`, press **Envoi**.

This is a test card in the television sense: a page whose correct appearance is
known, and *printed on the page itself*. Each line exercises one thing that
really breaks, and states what it must look like ("attendu: 20 tirets
identiques"). You don't need to know Videotex to use it — you only need to
compare what you see with what the page says you should see.

If everything matches, your chain is good, and you can stop suspecting your
hardware.

## What a wrong line means

| The line that's wrong | What it usually means |
|---|---|
| **ACCENTS** — `ÉÈÀÇÔÏ` comes out as garbage, or you see a backwards `?` | Framing. Something opened the port at 8N1 instead of **7E1**. This is the classic Minitel symptom. |
| **MOSAIQUE** — the bar has holes, or shows letters instead of blocks | The semigraphic (G1) set isn't being entered or left correctly — an `SO`/`SI` problem. |
| **REPETITION** — you get one dash, or the wrong count | The `REP` run-length fill isn't being expanded. |
| **The 40-column bar** — it wraps, or doesn't reach both edges | Cursor positioning, or a terminal that isn't in 40-column mode. |
| **INVERSE / CLIGNOTANT** — no inverse video, no blink | Display attributes aren't arriving. On a monochrome set, colours appear as grey levels — that is correct, not a fault. |
| **Nothing appears at all** | Not a rendering problem. Check the report card: cable, driver, and whether something else already has the serial port open (only one program can). |

A photograph of a wrong test card is enough to report a bug — it says exactly
which stage of the chain failed, which a screenshot of a garbled service never
could.

## Two gotchas worth knowing

**Only one program can hold the serial port.** If the Workbench window is open
and connected, a command-line `minitel connect` in a terminal will find the port
busy — or worse, quietly compete for the same bytes. Close one before using the
other. (This cost the author an afternoon of chasing a hardware fault that
wasn't there.)

**Nothing echoes what you type.** Workbench turns the Minitel's local echo off
deliberately, so that services which echo — MiniPavi and Retrocampus both do —
don't double every character. It follows that with *no* service connected,
typing on the Minitel produces nothing on screen. That is not a broken keyboard;
there is simply nobody to answer. Connect the demo and it will.
