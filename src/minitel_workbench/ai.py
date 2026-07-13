"""AI-assisted Videotex page generation.

The AI never emits raw Videotex control bytes (LLMs get those wrong). Instead it
returns a small JSON *page spec* — title, lines, colours — which
``videotex.page.build_page`` turns into correct bytes. That division keeps the
output valid on any terminal.

Provider order follows the Constitution: **Mistral first** (this project has
French roots), then ChatGPT, then a dependency-free offline template so the
feature does *something* useful even with no API key. Providers use only the
standard library (``urllib``) — no extra dependencies.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Protocol

_SYSTEM_PROMPT = (
    "You design pages for a 1980s French Minitel (Videotex), 40 columns wide, "
    "24 rows. Reply with ONLY a compact JSON object, no prose, no code fence, "
    'shaped like: {"title": str, "lines": [{"text": str, "colour": '
    'one of black/red/green/yellow/blue/magenta/cyan/white}], "footer": str}. '
    "Keep every text field <= 38 characters. Use plain ASCII (no accents). "
    "Prefer 6-14 short lines."
)


class Provider(Protocol):
    name: str

    def generate(self, prompt: str) -> dict: ...


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of a model reply that may include fences/prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


class _HTTPChatProvider:
    """Shared OpenAI-compatible chat-completions client (Mistral & OpenAI both
    speak this shape)."""

    name = "http"
    endpoint = ""
    model = ""

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def generate(self, prompt: str) -> dict:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }
        ).encode()
        req = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            raise RuntimeError(f"{self.name} API error {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise RuntimeError(f"Could not reach {self.name}: {exc.reason}") from exc
        content = payload["choices"][0]["message"]["content"]
        return _extract_json(content)


class MistralProvider(_HTTPChatProvider):
    name = "Mistral"
    endpoint = "https://api.mistral.ai/v1/chat/completions"
    model = "mistral-small-latest"


class OpenAIProvider(_HTTPChatProvider):
    name = "ChatGPT"
    endpoint = "https://api.openai.com/v1/chat/completions"
    model = "gpt-4o-mini"


class OfflineProvider:
    """No API key needed. Produces a simple, honest placeholder page from the
    prompt so the feature is never a dead end."""

    name = "offline"

    def generate(self, prompt: str) -> dict:
        words = prompt.strip().split()
        title = " ".join(words[:4]).upper()[:38] or "PAGE"
        lines = [{"text": prompt.strip()[:38]}]
        lines.append({"text": "", "colour": "white"})
        lines.append({"text": "Generated offline (no AI key).", "colour": "cyan"})
        lines.append({"text": "Set MISTRAL_API_KEY for real", "colour": "cyan"})
        lines.append({"text": "AI generation.", "colour": "cyan"})
        return {"title": title, "lines": lines, "footer": "SOMMAIRE pour revenir"}


def default_provider() -> Provider:
    """Pick a provider from the environment — Mistral first (Constitution)."""
    if os.environ.get("MISTRAL_API_KEY"):
        return MistralProvider(os.environ["MISTRAL_API_KEY"])
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIProvider(os.environ["OPENAI_API_KEY"])
    return OfflineProvider()


def generate_page_spec(prompt: str, provider: Provider | None = None) -> dict:
    """Return a page spec dict for ``prompt`` using ``provider`` (or the default)."""
    provider = provider or default_provider()
    spec = provider.generate(prompt)
    if not isinstance(spec, dict) or "title" not in spec:
        raise ValueError(f"{provider.name} did not return a usable page spec")
    return spec
