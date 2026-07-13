"""Recording -> stream reconstruction, and viewing a .vdt through the decoder."""

from minitel_workbench.recording import Recorder, stream_from_recording
from minitel_workbench.videotex import constants as C
from minitel_workbench.videotex.decoder import Decoder


def test_stream_reconstruction_by_direction(tmp_path):
    path = tmp_path / "s.mtr"
    rec = Recorder(path, service="X", clock=lambda: 0.0)
    rec.from_service(bytes([C.FF]) + b"PAGE")
    rec.from_terminal(C.function_key_sequence(C.Key.ENVOI))
    rec.from_service(b"MORE")
    rec.close()

    display = stream_from_recording(path, "service->terminal")
    typed = stream_from_recording(path, "terminal->service")
    assert display == bytes([C.FF]) + b"PAGE" + b"MORE"
    assert typed == C.function_key_sequence(C.Key.ENVOI)


def test_view_a_recording_renders_pages(tmp_path):
    path = tmp_path / "s.mtr"
    rec = Recorder(path, service="X", clock=lambda: 0.0)
    rec.from_service(bytes([C.FF, C.US, 0x41, 0x41]) + b"HELLO")
    rec.close()

    d = Decoder()
    d.feed(stream_from_recording(path))
    assert d.screen.line(0).startswith("HELLO")
