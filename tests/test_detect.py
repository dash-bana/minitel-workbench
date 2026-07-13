from minitel_workbench.hardware import detect
from minitel_workbench.hardware.detect import DetectedAdapter, best_adapter, find_minitel_adapters


def _adapter(device, serial, likely=True):
    return DetectedAdapter(
        device=device,
        likely_minitel=likely,
        advanced={"serial_number": serial, "device": device},
    )


def test_same_serial_collapses_to_one_stable_named(monkeypatch):
    # One physical FT232R shown under two macOS nodes with the same serial.
    monkeypatch.setattr(
        detect,
        "_from_pyserial",
        lambda: [
            _adapter("/dev/cu.usbserial-4", "A5XK3RJT"),
            _adapter("/dev/cu.usbserial-A5XK3RJT", "A5XK3RJT"),
        ],
    )
    res = find_minitel_adapters()
    assert len(res) == 1
    assert res[0].device == "/dev/cu.usbserial-A5XK3RJT"  # serial-named preferred
    assert best_adapter().device == "/dev/cu.usbserial-A5XK3RJT"


def test_distinct_serials_are_both_kept(monkeypatch):
    monkeypatch.setattr(
        detect,
        "_from_pyserial",
        lambda: [
            _adapter("/dev/cu.usbserial-A", "AAA"),
            _adapter("/dev/cu.usbserial-B", "BBB"),
        ],
    )
    assert len(find_minitel_adapters()) == 2


def test_likely_minitel_sorts_first(monkeypatch):
    monkeypatch.setattr(
        detect,
        "_from_pyserial",
        lambda: [
            DetectedAdapter(device="/dev/cu.Bluetooth", likely_minitel=False, advanced={}),
            _adapter("/dev/cu.usbserial-A5XK3RJT", "A5XK3RJT"),
        ],
    )
    assert find_minitel_adapters()[0].likely_minitel is True
