# The Minitel Workbench Constitution

> An open-source toolkit for preserving and extending the Minitel ecosystem.

This document is the project's constitution. It records the decisions that
were made deliberately, so that contributors — and automated agents — never
have to guess. Code and features come and go; these principles do not change
without a deliberate amendment and a good reason.

It is distilled from a long design conversation (`docs/design/design-notebook.md`).
When code and this document disagree, this document wins, and the code is a bug.

---

## 1. What Minitel Workbench *is*

Everything a Minitel owner needs, in one application — **regardless of how they
connect**. It is the front door to the surviving Minitel community: services,
documentation, history, diagnostics, and creation tools.

## 2. What Minitel Workbench is *not*

- It is **not** "a better bridge." The USB/serial bridge is *one module*, not
  the identity of the project.
- It is **not** a general retro-terminal suite. No VT100, Commodore, ANSI-BBS,
  or Amiga support. Relentless focus on the Minitel ecosystem is the point.
- It is **not** one person's project. It is a community project.

---

## The Commandments

These are load-bearing. Violating one is a design defect, not a style choice.

### I. Describe what the user *has*, not how it is implemented.
- ✅ "Minitel detected"  ❌ "FT232R enumerated"
- ✅ "Connected to Retrocampus"  ❌ "TCP socket established"
- ✅ "Keyboard responding"  ❌ "Serial RX active"

Users do not know or care about FTDI, USB-UART, RS-232, DIN-5, DriverKit, or
`/dev/cu.usbserial-*`. "DIN" and "FTDI" confuse most owners. Implementation
detail lives under an **Advanced/Diagnostics** disclosure, never in the normal
path.

### II. The telephone user is the primary audience.
90–95% of living Minitels still connect by telephone, not USB. The app must be
**fully useful with no cable and no serial port present**: service directory,
telephone dialing assistant, documentation, museum, emulator, page archive,
service status monitor, and AI help all work without hardware. Owning the USB
adapter *unlocks* extra tools (mirror, recording, diagnostics, benchmark) — it
is never a prerequisite, and nothing that already worked disappears.

### III. Never expose transport as the first decision.
Beginners choose a **destination** ("Retrocampus", "MiniPavi", "Local Demo",
"Add a service…"), never a transport ("Telnet / WebSocket / USB / Telephone").
The app figures out *how* to connect from the user's hardware and the service
definition. Transport selection is an advanced setting.

### IV. Never label a connection method "recommended."
Do not tell 95% of users they are using the second-best option. No
"USB/DIN (recommended)". State what is present, without judgement:
"Minitel detected" / "Telephone mode".

### V. Graceful degradation, never a lecture.
If a page uses features the terminal cannot show (color, DRCS, double-height),
render the best possible version silently — like a web browser degrading. No
pop-up, no warning, no "your Minitel is old." A capability report exists only
under Diagnostics, for users who go looking.

### VI. Never surface a limitation the user cannot act on.
- Good: "The Minitel isn't connected." (plug it in)
- Good: "Connection to Retrocampus was lost." (reconnect)
- Bad: "Your Minitel doesn't support color." (nothing to do)

### VII. Backward compatibility is sacred.
**A newer feature must never reduce compatibility with an older Minitel.**
The renderer and page tools use capability levels (L1 monochrome text +
semigraphics, L2 color, L3 DRCS, …). The app keeps an internal capability
profile per model and quietly does the right thing.

### VIII·b. AI is a service you connect to — Workbench never calls AI APIs.
"AI" in the Minitel world means a *service you connect to* (e.g. Retrocampus,
which offers Mistral and ChatGPT to Patreon supporters, reached by connecting the
Minitel to it). Workbench surfaces and routes to those services and credits them
(Mistral before ChatGPT) — but it does **not** call AI APIs itself, store or ship
API keys, or generate content on the user's behalf. This keeps the project free
of per-user billing, shared-key liability, and scope creep. Decided deliberately;
a built-in page generator was built and then removed to honour it.

### VIII. Community before technology.
Send traffic to the people who keep this ecosystem alive. Link to the museums
and archives rather than silently absorbing their work. Credit everyone.
Retrocampus is the featured default; MiniPavi is the featured gateway
alternative. Among AI services, **Mistral is listed before ChatGPT** (this
project has French roots).

### IX. Stay small at the edges, coherent at the core.
Core = transport + rendering + recording. Everything else (MiniPavi/Retrocampus
integration, browser emulator, AI page generation, telephone server, museum,
diagnostics) is a plugin/module around that core.

### X. The default answer is "link and attribute," not "redistribute."
Even where reuse is legal, record Title / Author / Source / License / Date, and
prefer linking until an author blesses redistribution.

---

## Product surface (target)

Top-level areas describe *goals*, not plumbing — no "serial", "telnet", "baud"
in the navigation:

`Services · Library · Studio · Diagnostics · Museum · AI · Community · Developer`

## Featured destinations

- **Retrocampus** — modern BBS by Francesco Sblendorio; free to access; AI
  (Mistral, ChatGPT) for Patreon subscribers. Featured default.
- **MiniPavi** — gateway/directory to hundreds of services. Featured alternative.
- **Local Demo** — offline, no hardware or network required. Proves the whole
  chain (keyboard, display, rendering) on its own.

## Known-good reference profile (the terminal this was born on)

```
Terminal : La Radiotechnique "Minitel 9" (NFZ 300), 1984, modem retournable
Link     : DIN-5  →  FT232R USB serial  →  Mac
Serial   : 1200 baud, 7 data bits, even parity, 1 stop bit (7E1), no flow control
Ceiling  : 1200 baud is the documented maximum for this generation's peri-port
```

The benchmark still probes higher speeds (300/1200/4800/9600/19200 × 7E1/8N1)
because Workbench serves *all* owners — it must always recover to 1200 7E1 and
report the measured stable maximum, not an optimistic spec.

---

## Amending this document

Change a commandment only by amending this file in a pull request that states
the reason. The design notebook is history; this file is current law.
