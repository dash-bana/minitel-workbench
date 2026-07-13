# Studio — make and serve your own pages

You don't need a terminal for any of this except the final `serve`.

## Generate a page with AI

```bash
minitel ai "a weather page for Paris, cyan title, 3-day forecast"
```

The model returns a small JSON *page spec* (title, lines, colours) and Workbench
turns it into correct Videotex — the AI never touches raw control bytes, so the
result is always valid. Provider order follows the project's roots: **Mistral
first**, then ChatGPT.

```bash
export MISTRAL_API_KEY=...          # real generation with Mistral
minitel ai "menu for a home dashboard: weather, mail, clock" --save home.vdt
minitel ai "1986-style news page" --html news.html   # colour screenshot
```

With no key set, it still works — it produces a simple offline placeholder page
and tells you how to enable real generation. Force a provider with
`--provider mistral|chatgpt|offline`.

## Preview a page

```bash
minitel view home.vdt              # in the terminal (colour if supported)
minitel view home.vdt --html home.html
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

## Inspect the bytes

```bash
minitel inspect home.vdt           # cursor moves, colours, text runs, named
```
