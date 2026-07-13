# Contributing to Minitel Workbench

Welcome — this is a community project for preserving and extending the Minitel
ecosystem. You don't need to be a French telematics historian or own a terminal
to help.

## Before you write code

Read the [Constitution](CONSTITUTION.md). It is short and it is binding. Most
review comments on this project will be a pointer to one of its commandments —
especially:

- **Describe what the user has, not how it's implemented** (no "FTDI"/"DIN"/
  "serial" in user-facing text).
- **The telephone user is primary** — core features must work with no cable.
- **Backward compatibility is sacred** — a new feature must never break an
  older Minitel.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,serial,ws]"
```

Everything except the `dev` extra is optional; the core and its tests run on the
standard library alone.

## Checks (Definition of Done)

Run before opening a PR:

```bash
ruff check .
black --check .
pytest
```

A change is "done" when: it imports cleanly with zero third-party packages,
tests pass, lint is clean, docs and `CHANGELOG.md` are updated, and there is no
known regression against older terminals.

## The golden test

The whole data path is exercisable with no hardware and no network via
`LoopbackLink` + `LocalDemoTransport`. If you touch the bridge, transports,
links, or the Videotex decoder, make sure `tests/test_end_to_end.py` still
passes and add coverage for your case.

## Adding a service to the directory

Most "new service" contributions are a single JSON object in
`src/minitel_workbench/services/directory.json`. Keep featured order and AI
ordering consistent with the Constitution (Retrocampus first; Mistral before
ChatGPT). Include a working `access` entry and a real `website`.

## Commits & PRs

- Conventional-commit style is appreciated (`feat:`, `fix:`, `docs:`…).
- Keep PRs focused. One feature, tests included.
- Credit people. This project sends traffic and thanks *upstream* — museums,
  service operators, adapter makers — rather than absorbing their work silently.

## Reporting hardware results

If you run Workbench against a physical Minitel, please open an issue with your
model, the measured stable serial speed, and anything that rendered wrong. Real
terminal reports are the most valuable contribution right now.
