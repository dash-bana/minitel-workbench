"""Load and query the service directory.

The directory is *data* (`directory.json`), not code, so the community can add a
destination without a release. This module gives it a small typed surface and
enforces the Constitution's ordering rules (featured first; the AI list keeps its
authored order, which places Mistral before ChatGPT).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class Service:
    """One destination in the directory."""

    id: str
    name: str
    description: str = ""
    featured: bool = False
    order: int = 999
    operator: str = ""
    language: str = ""
    tags: tuple[str, ...] = ()
    access: dict = field(default_factory=dict)
    alt_access: tuple[dict, ...] = ()
    ai_services: tuple[str, ...] = ()
    website: str = ""
    status: str = "unknown"

    @property
    def transport_kind(self) -> str:
        return self.access.get("kind", "unknown")

    @property
    def needs_hardware(self) -> bool:
        return False  # every listed transport works from the Mac side

    def telephone_numbers(self) -> list[str]:
        nums = [a["number"] for a in self.alt_access if a.get("kind") == "telephone"]
        if self.access.get("kind") == "telephone":
            nums.insert(0, self.access["number"])
        return nums

    @classmethod
    def from_dict(cls, raw: dict) -> Service:
        return cls(
            id=raw["id"],
            name=raw["name"],
            description=raw.get("description", ""),
            featured=raw.get("featured", False),
            order=raw.get("order", 999),
            operator=raw.get("operator", ""),
            language=raw.get("language", ""),
            tags=tuple(raw.get("tags", ())),
            access=raw.get("access", {}),
            alt_access=tuple(raw.get("alt_access", ())),
            ai_services=tuple(raw.get("ai_services", ())),
            website=raw.get("website", ""),
            status=raw.get("status", "unknown"),
        )


class ServiceDirectory:
    """A queryable collection of services."""

    def __init__(self, services: list[Service]) -> None:
        self._services = sorted(services, key=lambda s: (not s.featured, s.order, s.name))
        self._by_id = {s.id: s for s in self._services}

    def __iter__(self):
        return iter(self._services)

    def __len__(self) -> int:
        return len(self._services)

    def all(self) -> list[Service]:
        return list(self._services)

    def featured(self) -> list[Service]:
        return [s for s in self._services if s.featured]

    def get(self, service_id: str) -> Service | None:
        return self._by_id.get(service_id)

    def default(self) -> Service | None:
        """The default destination: first featured, else first of all."""
        featured = self.featured()
        return featured[0] if featured else (self._services[0] if self._services else None)


def _load_raw(path: Path | None) -> dict:
    if path is not None:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    text = (
        resources.files("minitel_workbench.services")
        .joinpath("directory.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def load_directory(path: Path | None = None) -> ServiceDirectory:
    """Load the built-in directory, or an override file if given."""
    raw = _load_raw(path)
    services = [Service.from_dict(item) for item in raw.get("services", [])]
    return ServiceDirectory(services)
