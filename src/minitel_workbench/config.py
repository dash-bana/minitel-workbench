"""Persistent settings.

The original GUI bridge forgot every setting on each launch; that was a real
source of frustration in the notebook. Workbench persists to a JSON file in the
platform config directory and never loses the user's choices.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "Minitel Workbench"


def config_dir() -> Path:
    """Platform config directory for the app."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":  # pragma: no cover - not exercised on CI
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def config_path() -> Path:
    return config_dir() / "settings.json"


def recordings_dir() -> Path:
    """Where session recordings go by default (matches the notebook's intent)."""
    return Path.home() / "Documents" / "Minitel Sessions"


@dataclass
class Settings:
    """User-visible, persisted settings. Deliberately free of transport jargon."""

    first_run_complete: bool = False
    default_service: str | None = None  # a service id from the directory
    #: Last serial device we used, so we can offer it again silently.
    last_serial_device: str | None = None
    record_sessions: bool = False
    #: Learned per-model capability, keyed by model id.
    model_profiles: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        path = path or config_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()
        known = {f for f in cls().__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in known})

    def save(self, path: Path | None = None) -> Path:
        path = path or config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        return path
