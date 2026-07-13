from minitel_workbench.videotex import constants as C


def test_local_echo_off_sequence_is_the_minitel_pro3_aiguillage():
    # ESC 3B 60 58 51 : PRO3, aiguillage OFF, screen(receiver), keyboard(emitter).
    assert C.LOCAL_ECHO_OFF == bytes([0x1B, 0x3B, 0x60, 0x58, 0x51])


def test_local_echo_on_only_differs_by_the_command_byte():
    assert C.LOCAL_ECHO_ON == bytes([0x1B, 0x3B, 0x61, 0x58, 0x51])
    assert C.LOCAL_ECHO_ON[:2] == C.LOCAL_ECHO_OFF[:2]
    assert C.LOCAL_ECHO_ON[3:] == C.LOCAL_ECHO_OFF[3:]
