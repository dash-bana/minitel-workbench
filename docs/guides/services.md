# Services & the directory

Workbench ships a curated directory of living Minitel destinations in
[`src/minitel_workbench/services/directory.json`](../../src/minitel_workbench/services/directory.json).
It's data, not code — adding a service is a one-object contribution.

## Featured

- **⭐ Retrocampus** — modern BBS by Francesco Sblendorio: forums, files, games,
  chat, and AI (Mistral, ChatGPT) for Patreon supporters. Free to access.
  Reached over WebSocket, and also by telephone. *This is the default.*
- **⭐ MiniPavi** — gateway/directory to hundreds of services. Its live in-terminal
  **Guide** is the authoritative list of current service codes (services come and
  go without the website changing). Reached over Telnet `go.minipavi.fr:516`.
- **⭐ Local Demo** — offline, no hardware or network. Proves the whole chain.

## Community

Also listed (status unverified — please report): LABBEJ27, HACKER, 3615co.de,
3611.re. Several are `ws://`-only, which is exactly why Workbench speaks
WebSocket as well as Telnet.

## Add a service

Open a [service submission issue](../../.github/ISSUE_TEMPLATE/service-submission.md)
or add an object to `directory.json`:

```json
{
  "id": "example",
  "name": "Example",
  "featured": false,
  "order": 20,
  "description": "One sentence about it.",
  "language": "fr",
  "tags": ["microserver"],
  "access": { "kind": "websocket", "url": "wss://example.example:8080" },
  "alt_access": [{ "kind": "telephone", "number": "+33 1 23 45 67 89" }],
  "website": "https://example.example",
  "status": "unverified"
}
```

`access.kind` may be `telnet`, `tcp`, `websocket`, `demo`, or `telephone`. Keep
featured order and any `ai_services` list consistent with the
[Constitution](../../CONSTITUTION.md) (Retrocampus first; Mistral before ChatGPT).

## A note on the ecosystem

The living Minitel world is small and generous. Workbench's job is to send people
**to** it — Retrocampus, MiniPavi, the Musée du Minitel, the folks who make the
adapters — not to absorb their work. For long-form history and galleries, the app
links out rather than flattening rich pages onto a 40-column screen. See the
Museum/Resources roadmap item.
