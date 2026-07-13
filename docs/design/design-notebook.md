# Origin

Minitel Workbench started as a hardware-debugging session: getting a 1984
La Radiotechnique Minitel back onto today's Internet through a USB serial cable on
a Mac. Solving each problem exposed the next — DriverKit and App Translocation,
FTDI serial enumeration, 7E1 framing (the infamous backwards `?`), Homebrew
Python without Tk, PEP 668, and finally a Videotex bridge to MiniPavi.

Somewhere in there it stopped being a fix and became a design conversation: what
would the toolkit the Minitel community never quite had look like? That
conversation's conclusions — the principles the project is bound by — are
captured deliberately in [`CONSTITUTION.md`](../../CONSTITUTION.md), and the
shape of the code in [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

The full original transcript is kept privately by the author; everything it
decided is reflected in this repository.
