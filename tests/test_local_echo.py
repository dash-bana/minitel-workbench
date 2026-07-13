from minitel_workbench.videotex import constants as C


def test_local_echo_off_matches_the_proven_pr0000_sequence():
    # ESC 3B 60 58 52 — the exact bytes the reference bridge sends (works on HW).
    assert C.LOCAL_ECHO_OFF == bytes([0x1B, 0x3B, 0x60, 0x58, 0x52])


def test_local_echo_on_only_differs_by_the_command_byte():
    assert C.LOCAL_ECHO_ON == bytes([0x1B, 0x3B, 0x61, 0x58, 0x52])
    assert C.LOCAL_ECHO_ON[:2] == C.LOCAL_ECHO_OFF[:2]
    assert C.LOCAL_ECHO_ON[3:] == C.LOCAL_ECHO_OFF[3:]
