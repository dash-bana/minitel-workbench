"""Command-line surface — always available, jargon kept out of normal output.

    minitel list      show destinations you can connect to
    minitel scan      look for a Minitel connection (no cable is fine)
    minitel doctor    check your setup and point at anything missing
    minitel demo      try the whole stack offline (no hardware, no network)
    minitel connect   connect a Minitel to a service

Everything except ``connect`` (to a real service) works with no hardware — the
telephone-only / no-terminal user is the primary audience (Constitution rule II).
"""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .config import Settings, recordings_dir
from .services import Service, load_directory


def _print_service(svc: Service, advanced: bool) -> None:
    star = "*" if svc.featured else " "
    print(f" {star} {svc.name:<14} {svc.description}")
    phones = svc.telephone_numbers()
    if phones:
        print(f"      telephone: {', '.join(phones)}")
    if svc.ai_services:
        print(f"      AI: {', '.join(svc.ai_services)}")
    if svc.website:
        print(f"      web: {svc.website}")
    if advanced:
        print(f"      id={svc.id}  transport={svc.transport_kind}  status={svc.status}")


def cmd_list(args: argparse.Namespace) -> int:
    directory = load_directory()
    print("Destinations you can connect to:\n")
    for svc in directory:
        _print_service(svc, args.advanced)
        print()
    print("Connect with:  minitel connect <name>   (e.g. minitel connect retrocampus)")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    from .hardware.detect import find_minitel_adapters

    adapters = find_minitel_adapters()
    if not adapters:
        print("No Minitel connection found.")
        print("That's normal — most Minitels connect by telephone, and everything")
        print("except live mirroring/recording works without a cable. Try:")
        print("    minitel demo")
        return 0

    print("Found:")
    for a in adapters:
        mark = "Minitel" if a.likely_minitel else "serial device"
        print(f"  - {a.label}  ({mark})")
        if args.advanced:
            for k, v in a.advanced.items():
                print(f"        {k}: {v}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"Minitel Workbench {__version__}\n")
    ok = "✓"
    no = "·"

    py = sys.version_info
    print(f"  {ok} Python {py.major}.{py.minor}.{py.micro}")

    def _have(mod: str) -> bool:
        try:
            __import__(mod)
            return True
        except Exception:
            return False

    have_serial = _have("serial")
    have_ws = _have("websocket")
    have_tk = _have("tkinter")

    print(
        f"  {ok if have_serial else no} Serial support "
        + ("ready" if have_serial else "not installed — needed only for a real cable")
    )
    print(
        f"  {ok if have_ws else no} WebSocket support "
        + ("ready" if have_ws else "not installed — needed for Retrocampus and ws:// services")
    )
    print(
        f"  {ok if have_tk else no} Desktop window (Tk) "
        + ("ready" if have_tk else "not installed — the command line works without it")
    )

    from .hardware.detect import best_adapter
    from .hardware.setup import usb_ftdi_present

    has_minitel = best_adapter() is not None
    driver_needed = not has_minitel and usb_ftdi_present()
    if has_minitel:
        print(f"  {ok} Minitel connection detected")
    elif driver_needed:
        print(f"  {no} Adapter plugged in, but its driver isn't installed — run: minitel setup")
    else:
        print(f"  {no} No Minitel connection detected (fine for telephone users)")

    settings = Settings.load()
    print(f"\n  Settings: {settings.default_service or 'no default yet'}")
    print(f"  Recordings: {recordings_dir()}")

    hints = []
    if not have_ws:
        hints.append('python -m pip install "minitel-workbench[ws]"    # for Retrocampus')
    if not have_serial and has_minitel:
        hints.append('python -m pip install "minitel-workbench[serial]" # for your cable')
    if hints:
        print("\nSuggested:")
        for h in hints:
            print(f"    {h}")
    return 0


def _drain(bridge, seconds: float = 0.4) -> None:
    """Pump a bridge until it goes quiet, so the demo screen settles."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and bridge.pump(timeout=0.05):
        pass


def cmd_selftest(args: argparse.Namespace) -> int:
    from .diagnostics import run

    print(f"Minitel Workbench {__version__} — your setup\n")
    print(run().text())
    print("\nSeeing a garbled screen? Connect the demo and open page 5, the test card.")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    from .bridge import Bridge
    from .hardware.link import LoopbackLink
    from .transport.local_demo import LocalDemoTransport
    from .videotex import constants as C
    from .videotex.decoder import Decoder

    link = LoopbackLink()
    transport = LocalDemoTransport()
    decoder = Decoder()
    bridge = Bridge(link, transport, monitor=decoder)
    color = sys.stdout.isatty()

    print("Offline demo — no Minitel and no network needed.")
    print("Type a code (1-4), then Enter. 's' = home menu, 'q' = quit.\n")
    _drain(bridge)
    print(decoder.screen.framed(color=color))

    try:
        while True:
            try:
                line = input("\ncode> ").strip()
            except EOFError:
                break
            if line == "q":
                break
            if line == "s":
                link.feed_key(C.function_key_sequence(C.Key.SOMMAIRE))
            else:
                link.feed_key(line.encode("ascii", "ignore"))
                link.feed_key(C.function_key_sequence(C.Key.ENVOI))
            _drain(bridge)
            print(decoder.screen.framed(color=color))
    finally:
        bridge.close()
    print("\nBye.")
    return 0


def _resolve_service(name: str) -> Service | None:
    directory = load_directory()
    return directory.get(name) or next(
        (s for s in directory if s.name.lower() == name.lower()), None
    )


def cmd_connect(args: argparse.Namespace) -> int:
    service = args.service
    if service is None:
        # No service given: fall back to the last-used one, else the default.
        service = Settings.load().default_service
        if service is None:
            directory = load_directory()
            default = directory.default()
            service = default.id if default else None
    if service is None:
        print("No service given and no default saved. Try: minitel connect minipavi")
        return 2

    svc = _resolve_service(service)
    if svc is None:
        print(f"Unknown service: {service!r}. See 'minitel list'.")
        return 2

    # The demo needs no hardware — route it straight to the offline experience.
    if svc.transport_kind == "demo":
        return cmd_demo(args)

    from .bridge import Bridge
    from .hardware.capability import profile_for_model
    from .hardware.detect import best_adapter
    from .hardware.link import SerialLink
    from .transport import UnsupportedTransport, build_transport
    from .videotex.decoder import Decoder

    adapter = best_adapter()
    if adapter is None:
        print("No Minitel connection found, so there's nothing to bridge to a service.")
        print("If your Minitel connects by telephone, dial the service on the terminal.")
        print("To try the software with no hardware:  minitel demo")
        return 1

    settings = Settings.load()
    profile = profile_for_model(None)
    print(f"Connecting your Minitel to {svc.name} …")
    try:
        link = SerialLink.open(adapter.device, profile)
    except RuntimeError as exc:
        print(str(exc))
        return 1

    # Stop the Minitel echoing its own keystrokes; the service echoes them back,
    # and both together double every character. --local-echo keeps it on for the
    # rare service that doesn't echo.
    if not args.local_echo:
        from .videotex import constants as C

        link.write(C.LOCAL_ECHO_OFF)
        # The terminal replies with a PRO acknowledgement on the keyboard
        # channel; drain it so the bridge doesn't forward it to the service as
        # spurious input (it would show up as typed characters, e.g. "CXM").
        time.sleep(0.3)
        for _ in range(50):
            if not link.read(256):
                break

    recorder = None
    if settings.record_sessions or args.record:
        from .recording import Recorder

        stamp = time.strftime("%Y%m%d-%H%M%S")
        path = recordings_dir() / f"{svc.id}-{stamp}.mtr"
        recorder = Recorder(path, service=svc.name)
        print(f"Recording this session to {path}")

    decoder = Decoder() if args.mirror else None
    settings.last_serial_device = adapter.device
    settings.default_service = svc.id
    settings.save()

    reconnect = not args.no_reconnect
    deadline = time.monotonic() + args.reconnect_for * 60
    print("Connected. Leave the Minitel at F (local mode). Press Ctrl-C here to stop.")
    if reconnect:
        print(
            f"If the service drops the session, it reconnects automatically "
            f"(for up to {args.reconnect_for} min)."
        )
    print()

    stopped = False
    first = True
    try:
        while not stopped:
            try:
                transport = build_transport(svc.access, name=svc.name)
            except (UnsupportedTransport, RuntimeError) as exc:
                print(str(exc))
                break
            if not first:
                print("Reconnected.")
            first = False

            bridge = Bridge(
                link,
                transport,
                recorder=recorder,
                monitor=decoder,
                close_link=False,
                close_recorder=False,
            )
            bridge.run()  # returns when the service closes the connection

            if not reconnect or time.monotonic() >= deadline:
                break
            print("Service dropped the session — reconnecting in 2s … (Ctrl-C to stop)")
            time.sleep(2)
    except KeyboardInterrupt:
        stopped = True
    finally:
        link.close()
        if recorder is not None:
            recorder.close()

    if decoder is not None:
        print("\nLast screen:")
        print(decoder.screen.framed(color=sys.stdout.isatty()))
    print("Disconnected.")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    from .benchmark import (
        EXPERIMENTAL_SPEEDS,
        STANDARD_SPEEDS,
        SpeedVerdict,
        make_throughput_payload,
        measure_loopback,
        run_sweep,
        theoretical_cps,
    )
    from .hardware.capability import profile_for_model
    from .hardware.detect import best_adapter
    from .hardware.link import SerialLink

    adapter = best_adapter()
    if adapter is None:
        print("No Minitel connection found — the benchmark needs the cable.")
        return 1

    profile = profile_for_model(None)

    def open_at(baud: int, _framing: str) -> SerialLink:
        return SerialLink.open(adapter.device, profile, speed=baud)

    interactive = sys.stdout.isatty() and sys.stdin.isatty()

    if args.loopback:
        # Real measurement — but only with a TX<->RX jumper on the adapter.
        payload = make_throughput_payload(args.bytes)
        print(f"Loopback test at 1200 7E1 ({args.bytes} bytes). Needs a TX↔RX jumper.")
        link = open_at(1200, "7E1")
        try:
            result = measure_loopback(link, payload, timeout=max(10.0, args.bytes / 60))
        finally:
            link.close()
        if result is None:
            print("\n  No bytes came back — is the TX↔RX loopback jumper in place?")
            print("  (This tests the adapter/cable, not a Minitel.)")
            return 1
        print(f"\n  {result.chars_per_sec:6.1f} chars/sec round-trip over {result.seconds:.1f}s")
        return 0

    if not args.all:
        # An honest baseline. The host CANNOT time a buffered, non-echoing link,
        # so we report the theoretical ceiling and say why.
        cps = theoretical_cps(1200, "7E1")
        print("Minitel serial link — 1200 baud, 7E1\n")
        print(f"  theoretical throughput: {cps:.0f} chars/sec (10 bits per character)")
        print(f"  a full 1000-char page:  ≈ {1000 / cps:.1f}s")
        print(
            "\n  Note: a USB serial adapter buffers all output and the Minitel does"
            "\n  not echo in local mode, so the host cannot time the wire directly."
            "\n  To measure an adapter empirically, use --loopback with a TX↔RX jumper."
            "\n  To see which speeds your terminal renders, use --all (watch the screen)."
        )
        return 0

    speeds = STANDARD_SPEEDS + (EXPERIMENTAL_SPEEDS if args.experimental else ())
    print("Full speed sweep. A labelled test page is sent at each speed.")
    print("Your Minitel's peripheral port has a fixed speed, so higher speeds")
    print("will likely garble — that's expected and safe; it always returns to")
    print("1200 7E1 at the end.\n")

    def verify(baud: int, framing: str) -> str:
        if not interactive:
            return "skipped"
        ans = (
            input(
                f"  {baud} {framing}: look at the Minitel — [c]lean / [g]arbled / "
                f"[n]othing / [s]kip? "
            )
            .strip()
            .lower()
        )
        return {"c": "clean", "g": "garbled", "n": "nothing", "s": "skipped"}.get(ans, "skipped")

    verdicts: list[SpeedVerdict] = run_sweep(open_at, speeds, verify)

    print("\n  MINITEL CAPABILITY REPORT")
    print("  (speed shows the theoretical rate; the verdict is what you saw)\n")
    clean = []
    for v in verdicts:
        cps = f"{theoretical_cps(v.baud, v.framing):5.0f} cps"
        print(f"    {v.baud:>6} {v.framing}   {cps}   {v.rendering}")
        if v.rendering == "clean":
            clean.append(v.baud)
    best = max(clean) if clean else 1200
    print(f"\n  Maximum verified clean speed: {best} baud")
    print("  Link restored to 1200 7E1.")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .bridge import Bridge
    from .transport.menu_server import MenuServerTransport, load_pages_from_dir

    pages = load_pages_from_dir(args.directory)
    if not pages:
        print(f"No .vdt pages found in {args.directory!r}.")
        print("Add .vdt Videotex pages to that folder (build them by hand or with any tool).")
        return 1

    server = MenuServerTransport(pages, title=args.title)

    if args.preview:
        # Render the menu locally with no hardware, for a quick look.
        from .hardware.link import LoopbackLink
        from .videotex.decoder import Decoder

        link = LoopbackLink()
        decoder = Decoder()
        bridge = Bridge(link, server, monitor=decoder)
        for _ in range(12):
            bridge.pump(timeout=0.05)
        print(f"Menu preview ({len(pages)} page(s)):\n")
        print(decoder.screen.framed(color=sys.stdout.isatty()))
        bridge.close()
        return 0

    from .hardware.capability import profile_for_model
    from .hardware.detect import best_adapter
    from .hardware.link import SerialLink

    adapter = best_adapter()
    if adapter is None:
        print("No Minitel connection found. To preview the menu with no hardware:")
        print(f"    minitel serve {args.directory} --preview")
        server.close()
        return 1

    link = SerialLink.open(adapter.device, profile_for_model(None))
    bridge = Bridge(link, server)
    print(f"Serving {len(pages)} page(s) to your Minitel. Leave it at F. Ctrl-C to stop.\n")
    try:
        bridge.run()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.close()
    print("Stopped.")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    import time

    from .hardware.setup import (
        DRIVER_MISSING,
        FTDI_VCP_URL,
        READY,
        detect,
        find_installer,
        guidance,
        open_privacy_settings,
        prepare_installer,
    )

    print("Checking your Minitel connection…\n")
    st = detect()
    installer = find_installer() if st.state == DRIVER_MISSING else None
    for line in guidance(st, installer):
        print(line)

    if args.install and st.state == DRIVER_MISSING:
        if not installer:
            print(f"\nNo installer found — download it first: {FTDI_VCP_URL}")
            return 1
        print("\nCopying the installer into /Applications (you'll be asked for your password)…")
        ok, msg = prepare_installer(installer)
        print(msg)
        if ok:
            open_privacy_settings()
            print("Opened System Settings — click Allow for the FTDI extension.")

    if args.watch and st.state != READY:
        print("\nWatching for the driver to come online… (Ctrl-C to stop)")
        try:
            while True:
                time.sleep(3)
                s = detect()
                if s.state == READY:
                    print(
                        "\n✓ Driver active — your Minitel connection is ready! Try: minitel connect"
                    )
                    break
                print(f"  … not yet (adapter={s.usb_present}, driver={s.driver_active})")
        except KeyboardInterrupt:
            print()
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    import time

    from .hardware.capability import profile_for_model
    from .hardware.detect import best_adapter
    from .hardware.link import SerialLink
    from .videotex import constants as C

    adapter = best_adapter()
    if adapter is None:
        print("No Minitel connection found.")
        return 1
    link = SerialLink.open(adapter.device, profile_for_model(None))
    seq = bytearray()
    seq += bytes([C.ESC, 0x4C, C.SI, C.FF])  # normal size, text set (G0), clear content + home
    # FF leaves the status line (row 0) untouched — clear it explicitly.
    # Row 0 col 1 is US 0x40 0x41; CAN fills to end of the row with spaces.
    seq += bytes([C.US, 0x40, 0x41, C.CAN])
    seq += bytes([C.US, C.POS_OFFSET + 1, C.POS_OFFSET + 1])  # cursor back to content home
    link.write(bytes(seq))
    time.sleep(0.3)
    link.close()
    print("Cleared the Minitel screen (content + status line).")
    print("The F in the top-right is the terminal's local-mode indicator — that stays.")
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    svc = _resolve_service(args.service)
    if svc is None:
        print(f"Unknown service: {args.service!r}. See 'minitel list'.")
        return 2
    from .telephone import dialing_instructions

    print(dialing_instructions(svc))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from .status import OFFLINE, ONLINE, check_all

    directory = load_directory()
    print("Checking services … (this makes outbound connections)\n")
    marks = {ONLINE: "●", OFFLINE: "○"}
    for st in check_all(directory, timeout=args.timeout):
        mark = marks.get(st.state, "◌")
        print(f"  {mark} {st.name:<14} {st.state:<8} {st.detail}")
    print("\n  ● online   ○ offline   ◌ unknown (e.g. telephone-only)")
    return 0


def cmd_resources(args: argparse.Namespace) -> int:
    from .resources import get_resource, load_resources

    if args.open:
        res = get_resource(args.open)
        if res is None:
            print(f"Unknown resource: {args.open!r}")
            return 2
        import webbrowser

        print(f"Opening {res.title} → {res.url}")
        webbrowser.open(res.url)
        return 0

    print("Explore Minitel history and preservation:\n")
    last_kind = None
    for res in load_resources():
        if res.kind != last_kind:
            print(f"  [{res.kind}]")
            last_kind = res.kind
        print(f"    {res.title}")
        print(f"      {res.url}")
        if res.note:
            print(f"      {res.note}")
        if args.advanced:
            print(f"      id={res.id}")
        print()
    print("Open one in your browser:  minitel resources --open <id>   (add --advanced for ids)")
    return 0


def _load_stream(path: str, direction: str) -> bytes:
    """Bytes from a raw ``.vdt`` dump, or one direction of a ``.mtr`` recording."""
    if path.endswith(".mtr"):
        from .recording import stream_from_recording

        return stream_from_recording(path, direction)
    with open(path, "rb") as fh:
        return fh.read()


def cmd_view(args: argparse.Namespace) -> int:
    from .videotex.decoder import Decoder

    data = _load_stream(args.file, "service->terminal")

    if args.filmstrip:
        from .monitor.filmstrip import build_filmstrip

        with open(args.filmstrip, "w", encoding="utf-8") as fh:
            fh.write(build_filmstrip(data, title=args.file))
        print(f"Wrote {args.filmstrip} (every page the session displayed)")
        return 0

    decoder = Decoder()
    decoder.feed(data)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(decoder.screen.to_html(title=args.file))
        print(f"Wrote {args.html}")
    else:
        print(decoder.screen.framed(color=sys.stdout.isatty()))
    return 0


_DIRECTIONS = {"shown": "service->terminal", "typed": "terminal->service"}


def cmd_inspect(args: argparse.Namespace) -> int:
    from .videotex.protocol import describe_stream, format_events

    data = _load_stream(args.file, _DIRECTIONS[args.direction])
    events = describe_stream(data)
    print(f"{len(data)} bytes, {len(events)} events:\n")
    print(format_events(events))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minitel",
        description="Minitel Workbench — a toolkit for the Minitel ecosystem.",
    )
    parser.add_argument("--version", action="version", version=f"Minitel Workbench {__version__}")
    parser.add_argument(
        "--advanced", action="store_true", help="show implementation detail (device paths, etc.)"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="show destinations").set_defaults(func=cmd_list)
    sub.add_parser("scan", help="look for a Minitel connection").set_defaults(func=cmd_scan)
    sub.add_parser("doctor", help="check your setup").set_defaults(func=cmd_doctor)
    sub.add_parser("demo", help="try the whole stack offline").set_defaults(func=cmd_demo)
    sub.add_parser(
        "selftest", help="report card: what's connected, how fast, and what it is"
    ).set_defaults(func=cmd_selftest)
    sub.add_parser("clear", help="clear a garbled Minitel screen").set_defaults(func=cmd_clear)

    p_setup = sub.add_parser("setup", help="detect the cable/driver and guide first-time setup")
    p_setup.add_argument(
        "--install",
        action="store_true",
        help="copy & launch the FTDI installer (asks for password)",
    )
    p_setup.add_argument(
        "--watch", action="store_true", help="wait and report when the driver comes online"
    )
    p_setup.set_defaults(func=cmd_setup)

    p_call = sub.add_parser("call", help="how to reach a service by telephone")
    p_call.add_argument("service", help="service id or name")
    p_call.set_defaults(func=cmd_call)

    p_status = sub.add_parser("status", help="check which services are online")
    p_status.add_argument("--timeout", type=float, default=5.0, help="probe timeout (seconds)")
    p_status.set_defaults(func=cmd_status)

    p_serve = sub.add_parser("serve", help="serve local .vdt pages to your Minitel")
    p_serve.add_argument("directory", help="folder of .vdt pages to serve")
    p_serve.add_argument("--title", default="MINITEL WORKBENCH", help="menu title")
    p_serve.add_argument("--preview", action="store_true", help="show the menu with no hardware")
    p_serve.set_defaults(func=cmd_serve)

    p_bench = sub.add_parser("benchmark", help="measure your Minitel's serial link")
    p_bench.add_argument("--all", action="store_true", help="sweep all standard speeds")
    p_bench.add_argument(
        "--experimental", action="store_true", help="also try experimental speeds (19200+)"
    )
    p_bench.add_argument(
        "--bytes",
        type=int,
        default=2000,
        help="payload size for the loopback test (default 2000)",
    )
    p_bench.add_argument(
        "--loopback",
        action="store_true",
        help="measure real throughput via a TX↔RX jumper (tests the adapter, not a Minitel)",
    )
    p_bench.set_defaults(func=cmd_benchmark)

    p_resources = sub.add_parser("resources", help="museums, history, and community links")
    p_resources.add_argument("--open", metavar="ID", help="open a resource in your browser")
    p_resources.set_defaults(func=cmd_resources)

    p_view = sub.add_parser("view", help="render a .vdt page or .mtr recording")
    p_view.add_argument("file", help="a .vdt Videotex dump or a .mtr recording")
    p_view.add_argument("--html", metavar="PATH", help="write a colour HTML screenshot instead")
    p_view.add_argument(
        "--filmstrip",
        metavar="PATH",
        help="write an HTML page showing every screen the session displayed",
    )
    p_view.set_defaults(func=cmd_view)

    p_inspect = sub.add_parser("inspect", help="annotate the bytes of a page/recording")
    p_inspect.add_argument("file", help="a .vdt dump or a .mtr recording")
    p_inspect.add_argument(
        "--direction",
        default="shown",
        choices=["shown", "typed"],
        help="for .mtr recordings: 'shown' (service→Minitel) or 'typed' (keyboard→service)",
    )
    p_inspect.set_defaults(func=cmd_inspect)

    p_connect = sub.add_parser("connect", help="connect a Minitel to a service")
    p_connect.add_argument(
        "service",
        nargs="?",
        default=None,
        help="service id or name (default: last used, e.g. minipavi)",
    )
    p_connect.add_argument("--mirror", action="store_true", help="show the last screen on exit")
    p_connect.add_argument("--record", action="store_true", help="record this session")
    p_connect.add_argument(
        "--local-echo",
        action="store_true",
        help="keep the Minitel's local echo on (only for services that don't echo)",
    )
    p_connect.add_argument(
        "--no-reconnect", action="store_true", help="do not auto-reconnect if the service drops"
    )
    p_connect.add_argument(
        "--reconnect-for",
        type=int,
        default=60,
        metavar="MIN",
        help="keep auto-reconnecting for this many minutes (default 60)",
    )
    p_connect.set_defaults(func=cmd_connect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # Friendly default: a short welcome, not an error.
        print("Minitel Workbench — everything a Minitel owner needs, in one place.\n")
        print("  minitel list      what you can connect to")
        print("  minitel demo      try it now, no hardware needed")
        print("  minitel status    see which services are online")
        print("  minitel resources museums, history, community links")
        print("  minitel call <service>     reach it by telephone")
        print("  minitel connect [service]  connect a cabled Minitel (default: last used)")
        print("  minitel serve <dir>        serve your own pages to a Minitel")
        print("  minitel benchmark          measure the serial link\n")
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
