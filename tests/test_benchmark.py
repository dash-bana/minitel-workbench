from minitel_workbench.benchmark import (
    SAFE_FRAMING,
    SAFE_SPEED,
    make_test_payload,
    make_throughput_payload,
    measure_write_throughput,
    run_sweep,
)


def test_bits_per_char_and_theoretical():
    from minitel_workbench.benchmark import bits_per_char, theoretical_cps

    assert bits_per_char("7E1") == 10
    assert bits_per_char("8N1") == 10
    assert bits_per_char("7E2") == 11
    assert theoretical_cps(1200, "7E1") == 120.0
    assert theoretical_cps(4800, "7E1") == 480.0


class _EchoLink:
    def __init__(self):
        self._buf = bytearray()

    def write(self, data):
        self._buf.extend(data)

    def read(self, n=4096):
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def close(self):
        pass


def test_measure_loopback_success_when_echoed():
    from minitel_workbench.benchmark import measure_loopback

    r = measure_loopback(_EchoLink(), b"HELLO", timeout=1.0)
    assert r is not None
    assert r.bytes_sent == 5


def test_measure_loopback_none_without_jumper():
    from minitel_workbench.benchmark import measure_loopback

    class Silent:
        def write(self, data):
            pass

        def read(self, n=4096):
            return b""

        def close(self):
            pass

    assert measure_loopback(Silent(), b"HELLO", timeout=0.2) is None


def test_throughput_payload_size_and_content():
    p = make_throughput_payload(2000)
    assert len(p) == 2001  # FF + 2000 bytes
    assert p[0] == 0x0C
    # Must be printable only (no control bytes that would skew a raw byte count).
    assert all(0x20 <= b <= 0x7E for b in p[1:])


class FakeLink:
    def __init__(self):
        self.written = bytearray()
        self.closed = False

    def write(self, data):
        self.written.extend(data)

    def close(self):
        self.closed = True


def test_throughput_math_with_fake_clock():
    link = FakeLink()
    ticks = iter([10.0, 11.0])  # 1 second elapsed
    payload = b"X" * 120
    r = measure_write_throughput(link, payload, baud=1200, framing="7E1", clock=lambda: next(ticks))
    assert r.bytes_sent == 120
    assert r.seconds == 1.0
    assert r.chars_per_sec == 120.0
    assert round(r.est_page_seconds(1200), 1) == 10.0  # 1200 bytes at 120 cps


def test_zero_elapsed_does_not_divide_by_zero():
    link = FakeLink()
    r = measure_write_throughput(link, b"AB", baud=1200, framing="7E1", clock=lambda: 5.0)
    assert r.chars_per_sec == float("inf")
    assert r.est_page_seconds() == 0.0


def test_test_payload_is_visible_videotex():
    p = make_test_payload("1200 7E1")
    assert p[0] == 0x0C  # starts by clearing the screen
    assert b"1200 7E1" in p


def test_sweep_always_recovers_to_1200_7e1():
    opened = []

    def open_at(baud, framing):
        opened.append((baud, framing))
        return FakeLink()

    verdicts = run_sweep(open_at, (300, 1200, 9600), verify=lambda b, f: "clean")
    assert [v.baud for v in verdicts] == [300, 1200, 9600]
    # The final open is the safe-recovery one.
    assert opened[-1] == (SAFE_SPEED, SAFE_FRAMING)


def test_sweep_recovers_even_if_verify_raises():
    opened = []

    def open_at(baud, framing):
        opened.append((baud, framing))
        return FakeLink()

    def boom(baud, framing):
        raise RuntimeError("user aborted")

    try:
        run_sweep(open_at, (4800,), verify=boom)
    except RuntimeError:
        pass
    # Recovery still ran despite the exception.
    assert opened[-1] == (SAFE_SPEED, SAFE_FRAMING)
