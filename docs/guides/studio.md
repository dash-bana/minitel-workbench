# Pages — make, view, and serve your own

You don't need a terminal for any of this except the final `serve`.

## Design principle: AI is a service you connect to

Minitel Workbench does **not** call AI APIs and never asks for an API key. "AI"
in the Minitel world means a *service you connect to* — for example Retrocampus,
which offers Mistral and ChatGPT to its Patreon supporters. You reach it by
connecting your Minitel to that service (`minitel connect retrocampus`); the AI
runs there, not here. See [`CONSTITUTION.md`](../../CONSTITUTION.md).

## Build a page

Pages are plain Videotex (`.vdt`) — a stream of the bytes a Minitel understands.
The `videotex.page` module builds valid pages from a simple spec, so you never
hand-write control codes:

```python
from minitel_workbench.videotex.page import build_page

page = build_page({
    "title": "METEO PARIS",
    "lines": [
        {"text": "Ciel clair", "colour": "cyan"},
        {"text": "18 degres"},
        {"text": "Vent 12 km/h SO"},
    ],
    "footer": "SOMMAIRE pour revenir",
})
open("weather.vdt", "wb").write(page)
```

Colour codes are ignored gracefully on a monochrome terminal (Constitution
rule VII), so the same page is safe on any model.

## Preview a page

```bash
minitel view weather.vdt              # in the terminal (colour if supported)
minitel view weather.vdt --html weather.html
minitel view session.mtr --filmstrip pages.html   # every screen of a recording
```

## Inspect the bytes

```bash
minitel inspect weather.vdt           # cursor moves, colours, text runs, named
```

## Serve your pages to a real Minitel

Put some `.vdt` files in a folder, then:

```bash
minitel serve ~/minitel-pages --title "DASH INFO"
```

Your Minitel shows a numbered menu; type a number + **ENVOI** to open a page,
**SOMMAIRE** to return. The Mac is now the service. Preview the menu with no
hardware:

```bash
minitel serve ~/minitel-pages --preview
```
