from minitel_workbench.config import Settings


def test_defaults():
    s = Settings()
    assert s.first_run_complete is False
    assert s.default_service is None
    assert s.record_sessions is False


def test_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    s = Settings(first_run_complete=True, default_service="retrocampus", record_sessions=True)
    s.save(path)
    loaded = Settings.load(path)
    assert loaded.first_run_complete is True
    assert loaded.default_service == "retrocampus"
    assert loaded.record_sessions is True


def test_missing_file_returns_defaults(tmp_path):
    assert Settings.load(tmp_path / "absent.json").default_service is None


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"default_service": "minipavi", "obsolete_key": 42}', encoding="utf-8")
    loaded = Settings.load(path)
    assert loaded.default_service == "minipavi"
