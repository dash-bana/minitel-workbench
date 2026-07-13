from minitel_workbench.services import load_directory


def test_directory_loads_and_has_featured():
    d = load_directory()
    assert len(d) >= 3
    featured = d.featured()
    assert featured, "expected at least one featured service"


def test_retrocampus_is_the_default_and_first_featured():
    d = load_directory()
    # Constitution: Retrocampus is the featured default.
    assert d.default().id == "retrocampus"
    assert d.featured()[0].id == "retrocampus"


def test_minipavi_is_featured_after_retrocampus():
    d = load_directory()
    ids = [s.id for s in d.featured()]
    assert ids.index("retrocampus") < ids.index("minipavi")


def test_ai_ordering_mistral_before_chatgpt():
    d = load_directory()
    retro = d.get("retrocampus")
    assert list(retro.ai_services).index("Mistral") < list(retro.ai_services).index("ChatGPT")


def test_demo_service_uses_demo_transport():
    d = load_directory()
    assert d.get("demo").transport_kind == "demo"


def test_lookup_by_id():
    d = load_directory()
    assert d.get("minipavi").access == {"kind": "telnet", "host": "go.minipavi.fr", "port": 516}
    assert d.get("nope") is None
