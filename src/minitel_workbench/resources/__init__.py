"""Curated external resources — museums, history, community, tools.

Workbench points people *to* the community's archives and credits them, rather
than flattening rich, graphics-heavy history onto a 40-column screen
(Constitution rules VIII and X). Resources open in the user's normal browser.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources as _res
from pathlib import Path

_KIND_ORDER = {"community": 0, "museum": 1, "history": 2, "article": 3, "tool": 4}


@dataclass(frozen=True)
class Resource:
    id: str
    title: str
    url: str
    kind: str = "history"
    language: str = ""
    note: str = ""


def load_resources(path: Path | None = None) -> list[Resource]:
    if path is not None:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        text = (
            _res.files("minitel_workbench.resources")
            .joinpath("resources.json")
            .read_text(encoding="utf-8")
        )
        raw = json.loads(text)
    items = [Resource(**r) for r in raw.get("resources", [])]
    items.sort(key=lambda r: (_KIND_ORDER.get(r.kind, 9), r.title))
    return items


def get_resource(resource_id: str, path: Path | None = None) -> Resource | None:
    return next((r for r in load_resources(path) if r.id == resource_id), None)
