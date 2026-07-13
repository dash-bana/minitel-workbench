# Minitel keyboard guide

Minitel menus are not modern web pages. You usually **type a number or service
code, then press ENVOI** — you don't highlight items with arrow keys. If more
information exists, the service sends a whole new page; **SUITE** requests it.

| Key | What it does |
|-----|--------------|
| **ENVOI** | Submit the typed code, number, or form (sends `13 41`) |
| **SOMMAIRE** | Back to the current service's main menu |
| **GUIDE** | Help / service guide |
| **SUITE** | Next page |
| **RETOUR** | Previous page |
| **RÉPÉTITION** | Redraw the current page |
| **CORRECTION** | Delete the previous character |
| **ANNULATION** | Clear the current entry |
| **CONNEXION/FIN** | End / change connection state — avoid it while using the USB bridge |
| **Shift + CONNEXION/FIN** | On MiniPavi, returns to the gateway home page |

Notes from real use:

- With local echo off (the usual bridge setting), a character only appears once
  the **service** echoes it back — so a keypress may seem to do nothing until the
  page updates. Wait for a page to finish drawing before typing; at 1200 baud a
  full page takes several seconds.
- Function keys transmit a two-byte sequence: a separator (`13`) followed by a
  code (ENVOI = `41`, SOMMAIRE = `46`, SUITE = `48`, …). Workbench's protocol
  view names these for you.
