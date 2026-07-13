from minitel_workbench.recording import Recorder, read_recording


def test_recording_round_trip(tmp_path):
    path = tmp_path / "session.mtr"
    # Deterministic clock so offsets are stable in the test.
    ticks = iter([0.0, 0.0, 0.5, 1.25])
    rec = Recorder(path, service="Local Demo", clock=lambda: next(ticks))
    rec.from_terminal(b"\x13\x41")  # ENVOI
    rec.from_service(b"\x0cHELLO")
    rec.close()

    events = read_recording(path)
    assert events[0]["type"] == "meta" and events[0]["service"] == "Local Demo"
    data = [e for e in events if e["type"] == "data"]
    assert data[0]["dir"] == "terminal->service" and data[0]["hex"] == "1341"
    assert data[1]["dir"] == "service->terminal" and data[1]["hex"] == "0c48454c4c4f"
    assert events[-1]["type"] == "meta" and "ended" in events[-1]
