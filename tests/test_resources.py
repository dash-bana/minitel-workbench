from minitel_workbench.resources import get_resource, load_resources


def test_resources_load_and_sort_community_first():
    items = load_resources()
    assert len(items) >= 6
    # Community links sort ahead of museum/history/tool.
    kinds = [r.kind for r in items]
    assert kinds.index("community") < kinds.index("museum")


def test_expected_resources_present():
    ids = {r.id for r in load_resources()}
    assert {"retrocampus", "minipavi", "musee-forum", "wikipedia-fr", "bridge-origin"} <= ids


def test_lookup_by_id():
    res = get_resource("musee-forum")
    assert res is not None
    assert res.url.startswith("https://forum.museeminitel.fr")


def test_all_resources_have_titles_and_urls():
    for r in load_resources():
        assert r.title and r.url.startswith("http")


def test_where_to_buy_a_cable_comes_first():
    """Someone with no cable is the least equipped to find one — so the pointer
    to it leads the list, and the setup wizard repeats it when no cable is found."""
    from minitel_workbench.hardware import setup

    items = load_resources()
    assert items[0].kind == "hardware"
    assert "cable" in items[0].id

    guidance = "\n".join(
        setup.guidance(setup.SetupState(setup.NO_ADAPTER, False, False, False), None)
    )
    assert setup.CABLE_URL in guidance
