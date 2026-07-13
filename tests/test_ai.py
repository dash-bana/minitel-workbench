import pytest

from minitel_workbench.ai import (
    MistralProvider,
    OfflineProvider,
    OpenAIProvider,
    _extract_json,
    default_provider,
    generate_page_spec,
)
from minitel_workbench.videotex.decoder import Decoder
from minitel_workbench.videotex.page import build_page


def test_extract_json_plain():
    assert _extract_json('{"title": "X"}') == {"title": "X"}


def test_extract_json_with_code_fence_and_prose():
    text = 'Sure!\n```json\n{"title": "METEO", "lines": []}\n```\n'
    assert _extract_json(text) == {"title": "METEO", "lines": []}


def test_offline_provider_is_usable_without_a_key():
    spec = OfflineProvider().generate("weather for paris")
    assert spec["title"] == "WEATHER FOR PARIS"
    # And it must build into a real page.
    d = Decoder()
    d.feed(build_page(spec))
    assert "WEATHER" in d.screen.text


def test_default_provider_prefers_mistral(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "m")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert isinstance(default_provider(), MistralProvider)


def test_default_provider_falls_back_to_openai_then_offline(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert isinstance(default_provider(), OpenAIProvider)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert isinstance(default_provider(), OfflineProvider)


class _FakeProvider:
    name = "fake"

    def generate(self, prompt):
        return {"title": prompt.upper(), "lines": [{"text": "ok", "colour": "green"}]}


def test_generate_page_spec_with_injected_provider():
    spec = generate_page_spec("hi", _FakeProvider())
    assert spec["title"] == "HI"


def test_generate_page_spec_rejects_bad_output():
    class Bad:
        name = "bad"

        def generate(self, prompt):
            return "not a dict"

    with pytest.raises(ValueError):
        generate_page_spec("x", Bad())


def test_endpoints_follow_constitution_order():
    # Mistral first: distinct, correct endpoints.
    assert "mistral.ai" in MistralProvider("k").endpoint
    assert "openai.com" in OpenAIProvider("k").endpoint
