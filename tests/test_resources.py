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
