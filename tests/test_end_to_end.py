"""End-to-end test: POS app -> RAW 9100 -> BonBridge -> printer.

Runs entirely without hardware by pointing the network transport at the mock
printer from ``tests/mock_printer.py``.

Usage::

    python3 tests/test_end_to_end.py
"""

from __future__ import annotations

import io
import json
import os
import socket
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

TMP = Path(tempfile.mkdtemp(prefix="bonbridge-test-"))
os.environ["BONBRIDGE_CONFIG_DIR"] = str(TMP / "etc")
os.environ["BONBRIDGE_CONFIG"] = str(TMP / "etc" / "config.yaml")
os.environ["BONBRIDGE_STATE_DIR"] = str(TMP / "state")
os.environ["BONBRIDGE_LOG_DIR"] = str(TMP / "log")
os.environ["BONBRIDGE_ROOT"] = str(ROOT)

from bonbridge import escpos, health, paths  # noqa: E402
from bonbridge.config import Config  # noqa: E402
from bonbridge.daemon import BonBridge  # noqa: E402
from bonbridge.web.server import WebServer  # noqa: E402
from mock_printer import MockPrinter  # noqa: E402

from bonbridge import netwatch as _netwatch  # noqa: E402

_REAL_SNAPSHOT = _netwatch.snapshot

RAW_PORT = 19100
WEB_PORT = 18080
PRINTER_PORT = 19200
ENPC_PORT = 13289

FAILURES = []


def check(condition: bool, label: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        FAILURES.append(label)


def get_json(path: str, method: str = "GET", payload=None):
    url = f"http://127.0.0.1:{WEB_PORT}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
        if response.headers.get_content_type() == "application/json":
            return json.loads(body)
        return body.decode("utf-8", "replace")


def check_thread_subclasses() -> None:
    """Our Thread subclasses must not shadow attributes of threading.Thread.

    Python 3.13 gave ``threading.Thread`` a private ``_handle`` attribute, which
    silently overwrote a method of the same name in the ENPC responder and
    killed the thread at runtime.  ``_stop`` is the same trap (Thread._stop is a
    method, we used to assign an Event).  This test makes the whole class of bug
    impossible to reintroduce, on every Python version.
    """
    import threading

    from bonbridge.discovery import EnpcResponder
    from bonbridge.jobs import PrinterWorker
    from bonbridge.raw_server import RawListenerSupervisor
    from bonbridge.web.server import WebServer

    reserved = {name for name in dir(threading.Thread)}
    for cls in (EnpcResponder, PrinterWorker, RawListenerSupervisor, WebServer):
        # Only private single-underscore names matter; dunders are compiler
        # bookkeeping (3.13 adds __firstlineno__ / __static_attributes__).
        own = {
            name
            for name in vars(cls)
            if name.startswith("_") and not name.startswith("__")
        }
        clashes = sorted(own & reserved)
        check(not clashes, f"{cls.__name__} does not shadow Thread attributes ({clashes})")

    # Attributes assigned in __init__ must not shadow Thread members either -
    # that is exactly how "self._stop = Event()" broke join()/is_alive().
    thread_methods = {name for name, value in vars(threading.Thread).items() if callable(value)}
    probe = RawListenerSupervisor("t", "127.0.0.1", 1, lambda *args: None)
    shadowed = sorted(name for name in vars(probe) if name in thread_methods)
    check(not shadowed, f"instance attributes do not shadow Thread methods ({shadowed})")


def check_system_info_cache() -> None:
    """Expensive readings must be cached - the overview is polled constantly.

    ``ip_addresses()`` forks ``ip`` and ``read_throttled()`` may fork
    ``vcgencmd``.  With a browser tab open, the overview endpoint asks for both
    every few seconds; on a single-core Pi 1 that is real load.
    """
    from bonbridge import sysinfo

    sysinfo.clear_cache()
    calls = []

    def producer() -> int:
        calls.append(1)
        return len(calls)

    values = [sysinfo.cached("unit-test", 60.0, producer) for _ in range(5)]
    check(values == [1, 1, 1, 1, 1] and len(calls) == 1, "cached() calls the producer once")
    check(sysinfo.cached("unit-test", 0, producer) == 2, "ttl=0 bypasses the cache")

    sysinfo.clear_cache()
    check(sysinfo.cached("unit-test", 60.0, producer) == 3, "clear_cache() drops the entry")

    sysinfo.clear_cache()
    started = time.time()
    for _ in range(50):
        sysinfo.ip_addresses()
        health.read_throttled()
    elapsed = time.time() - started
    check(elapsed < 0.5, f"50 cached overview readings stay cheap ({elapsed * 1000:.0f} ms)")



def check_network_watchdog() -> None:
    """The watchdog must report transitions once, not on every poll."""
    from bonbridge import netwatch

    state = netwatch.snapshot(gateway_check=False)
    check("online" in state and "reason" in state, "network snapshot has a verdict")
    check(isinstance(state.get("interfaces"), list), "network snapshot lists interfaces")

    events = []
    watcher = netwatch.NetworkWatcher(
        lambda online, snap, since: events.append(online), interval=3600, confirmations=2
    )
    fake_online = {"online": True, "reason": "online", "interfaces": [], "ip": "10.0.0.5"}
    fake_offline = {"online": False, "reason": "no_carrier", "interfaces": [], "ip": ""}

    netwatch.snapshot = lambda *a, **k: fake_online  # type: ignore[assignment]
    watcher.check_once()
    check(events == [], "no slip while the network is fine")

    netwatch.snapshot = lambda *a, **k: fake_offline  # type: ignore[assignment]
    watcher.check_once()
    check(events == [], "a single failed check does not trigger (anti-flapping)")
    watcher.check_once()
    check(events == [False], "the outage is reported after the second check")
    watcher.check_once()
    watcher.check_once()
    check(events == [False], "the outage is reported only once, not per poll")

    netwatch.snapshot = lambda *a, **k: fake_online  # type: ignore[assignment]
    watcher.check_once()
    watcher.check_once()
    check(events == [False, True], "the recovery is reported once")

    # A device that starts up without a network reports immediately.
    netwatch.snapshot = lambda *a, **k: fake_offline  # type: ignore[assignment]
    fresh_events = []
    fresh = netwatch.NetworkWatcher(
        lambda online, snap, since: fresh_events.append(online), interval=3600, confirmations=2
    )
    fresh.check_once()
    check(fresh_events == [False], "starting without a network reports straight away")

    netwatch.snapshot = _REAL_SNAPSHOT  # type: ignore[assignment]

    slip = escpos.network_alert_page(
        online=False, printer_name="Theke 1", reason="Kein Signal", columns=42,
        rows=[("eth0", "kein Signal")], timestamp="2026-08-20 10:00:00",
    )
    check(b"KEINE NETZWERKVERBINDUNG" in slip, "outage slip carries the heading")
    check(b"eth0" in slip, "outage slip lists the interface")
    back = escpos.network_alert_page(
        online=True, printer_name="Theke 1", columns=42, address="192.168.1.50", outage="7 min"
    )
    check(b"192.168.1.50" in back, "recovery slip carries the new address")


def check_profile_matching() -> None:
    """Model identification must use every identifier that is available."""
    from bonbridge import caps

    profile, reason = caps.match_profile({"manufacturer": "EPSON", "product": "TM-T88V"})
    check(profile == "TM-T88V", f"USB product string identifies the model (got {profile})")

    # The regression this guards: usblp connections only expose the model in
    # the IEEE-1284 device ID, which used to be collected but never matched.
    profile, reason = caps.match_profile(
        {"ieee1284_id": "MFG:EPSON;CMD:ESC/POS;MDL:TM-T88V;CLS:PRINTER;"}
    )
    check(profile == "TM-T88V", f"IEEE-1284 device ID identifies the model (got {profile})")

    profile, reason = caps.match_profile({"gs_i": {"model_text": "TM-T88V"}})
    check(profile == "TM-T88V", "the GS I reply identifies the model")

    profile, reason = caps.match_profile({})
    check(profile.startswith("generic"), "no identifier at all falls back to generic")
    check("Keine Modellkennung" in reason, "the fallback says why it fell back")

    from bonbridge import health

    checks = health.profile_check(
        {"capabilities": {"profile_id": "generic-80mm"}, "identity": {"product": ""}}
    )
    check(checks and checks[0]["level"] == "warn", "a generic profile is reported as a warning")


def check_updater() -> None:
    """Archive handling: what goes in must come out, and only if it is ours."""
    from bonbridge import updater

    check(updater.parse_version("v1.2.3") == (1, 2, 3), "version tags are parsed")
    check(updater.is_newer("1.10.0", "1.9.9"), "1.10 is newer than 1.9")
    check(not updater.is_newer("1.1.2", "1.1.2"), "the same version is not newer")

    work = TMP / "update"
    work.mkdir(parents=True, exist_ok=True)

    # A valid release archive round-trips and reports its version.
    good = work / "good.tar.gz"
    with tarfile.open(good, "w:gz") as archive:
        for name in ("install.sh", "VERSION", "src/bonbridge/__init__.py"):
            source = ROOT / name
            archive.add(source, arcname=f"Bonbridge-9.9.9/{name}")
    root = updater.extract(good, work / "out-good")
    check(root.name == "Bonbridge-9.9.9", "the source root inside the archive is found")
    check(updater.archive_version(root) != "", "the archive version is readable")

    # Something that is not BonBridge must be refused, not half-installed.
    bad = work / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as archive:
        info = tarfile.TarInfo("hello.txt")
        payload = b"not a release"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    try:
        updater.extract(bad, work / "out-bad")
        check(False, "a foreign archive is rejected")
    except ValueError:
        check(True, "a foreign archive is rejected")

    # Path traversal in a member name must not escape the target directory.
    evil = work / "evil.tar.gz"
    with tarfile.open(evil, "w:gz") as archive:
        info = tarfile.TarInfo("../escaped.txt")
        payload = b"x"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    try:
        updater.extract(evil, work / "out-evil")
        check(False, "an archive that escapes its directory is rejected")
    except ValueError:
        check(True, "an archive that escapes its directory is rejected")

    script = updater.build_runner_script(root, "9.9.9")
    text = script.read_text(encoding="utf-8")
    check("install.sh" in text and str(root) in text, "the runner script calls install.sh")


def check_image_printing() -> None:
    """The preview has to be the bitmap that is printed, not a lookalike."""
    from bonbridge import images

    if not images.HAVE_PIL:
        check(True, "image printing reports itself unavailable without Pillow")
        return

    from PIL import Image as PILImage

    source = PILImage.new("RGB", (200, 80), (255, 255, 255))
    for x in range(0, 200, 2):
        for y in range(0, 40):
            source.putpixel((x, y), (0, 0, 0))
    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    data = buffer.getvalue()

    result = images.rasterise(data, dots=576, dither=False, threshold=128)
    check(result["width"] == 576, f"the bitmap is padded to the print width ({result['width']})")
    check(result["preview_png"].startswith("data:image/png;base64,"), "the preview is a PNG")
    check(result["escpos"].startswith(b"\x1d\x76\x30\x00"), "GS v 0 raster command emitted")

    # Row count in the command header must match the actual bitmap height.
    header = result["escpos"][4:8]
    width_bytes = header[0] | (header[1] << 8)
    rows = header[2] | (header[3] << 8)
    check(width_bytes == 72, f"row width is 72 bytes for 576 dots (got {width_bytes})")
    check(rows == min(images.BAND_ROWS, result["height"]), "the band height matches the bitmap")

    check(images.sniff(data)[1] == "PNG", "PNG is recognised")
    check(images.sniff(b"%PDF-1.4 ...")[0] == "pdf", "a PDF is recognised and can be refused")


def main() -> int:
    printer = MockPrinter("127.0.0.1", PRINTER_PORT).start()
    print(f"mock printer on 127.0.0.1:{PRINTER_PORT}")

    config = Config(
        {
            "web": {"bind": "127.0.0.1", "port": WEB_PORT},
            "raw": {"port": RAW_PORT},
            "discovery": {"mdns": False, "enpc": True, "log_probes": True, "enpc_port": ENPC_PORT},
            "printers": [
                {
                    "id": "theke1",
                    "name": "Theke 1",
                    "bind": "127.0.0.1",
                    "profile": "TM-T88V",
                    "transport": {"type": "network", "host": "127.0.0.1", "port": PRINTER_PORT},
                    "options": {"status_polling": True, "status_interval": 2},
                }
            ],
        },
        path=paths.CONFIG_FILE,
    )

    app = BonBridge(config)
    app.start()
    web = WebServer(app, bind="127.0.0.1", port=WEB_PORT)
    web.start()
    time.sleep(2.0)

    try:
        # 0. structural check that survives Python upgrades
        check_thread_subclasses()
        check_system_info_cache()
        check_network_watchdog()
        check_profile_matching()
        check_updater()
        check_image_printing()

        # 1. the RAW listener accepts a job like a POS application would
        payload = b"\x1b@Bestellung Tisch 4\n2x Cola\n1x Pommes\n\n\n"
        with socket.create_connection(("127.0.0.1", RAW_PORT), timeout=5) as sock:
            sock.sendall(payload)
        time.sleep(1.5)
        check(b"Bestellung Tisch 4" in printer.data, "RAW job reached the printer")

        # 2. overview reports the printer as connected and healthy
        overview = get_json("/api/overview")
        entry = overview["printers"][0]
        check(entry["connected"] is True, "printer reported as connected")
        check(entry["jobs_total"] >= 1, "job counter incremented")
        check(entry["listener"]["listening"] is True, "RAW listener is listening")
        check(entry["pos_port"] == RAW_PORT, "POS port reported")
        check(entry["status_level"] in ("ok", "warn"), f"status level ok (got {entry['status_level']})")

        # 3. capabilities and POS recommendation
        caps = entry["capabilities"]
        check(caps["profile_id"] == "TM-T88V", "profile TM-T88V selected")
        recommendation = caps["recommendation"]
        check(recommendation["columns"] == 56, "recommended line width is 56")
        check(recommendation["font"] == "font2", "recommended font is font2")
        check(recommendation["codepage"] == "cp1252", "recommended code page is cp1252")
        check(caps["features"]["cutter"]["effective"] is True, "cutter detected")

        # 4. status read-back really works (mock answers DLE EOT)
        before = len(printer.data)
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(0.5)
        status = get_json("/api/printers/theke1")["printer"]["status"]
        check("paper" in status and "offline" in status, "DLE EOT status decoded")
        check(len(printer.data) > before, "status request was sent to the printer")

        # 5. simulate paper end and see the traffic light change
        printer.state.paper_end = True
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(0.3)
        entry = get_json("/api/printers/theke1")["printer"]
        check(entry["status_level"] == "error", "paper end raises an error state")
        check("paper_end" in (entry["status_messages"] or []), "paper end message key present")
        health = get_json("/api/health")["health"]
        check(health["level"] in ("error", "warn"), "health level follows the printer state")
        problems = health["printers"]["theke1"]["problems"]
        check(
            any("paper" in c["id"] for c in problems),
            "health explains the paper problem",
        )
        check(
            all(c["title_de"] and c["title_en"] for c in health["device"]["checks"]),
            "device checks are bilingual",
        )
        printer.state.paper_end = False

        # 6. test page contains the ruler and the special characters
        before = len(printer.data)
        get_json("/api/printers/theke1/test", method="POST", payload={"kind": "standard"})
        time.sleep(1.2)
        printed = printer.data[before:]
        check(b"56:" in printed, "test page contains the 56 character ruler")
        check(escpos.encode_text("ä", "cp1252") in printed, "umlaut encoded as cp1252")
        check(b"\x1dV" in printed, "test page ends with a cut command")

        # 7. feature override changes the effective value
        get_json(
            "/api/printers/theke1",
            method="PATCH",
            payload={"features": {"cutter": False}},
        )
        time.sleep(1.5)
        caps = get_json("/api/printers/theke1")["printer"]["capabilities"]
        check(caps["features"]["cutter"]["effective"] is False, "cutter override applied")
        check(caps["features"]["cutter"]["detected"] is True, "detection value preserved")

        # 8. no cut command when the feature is switched off
        before = len(printer.data)
        get_json("/api/printers/theke1/test", method="POST", payload={"kind": "minimal"})
        time.sleep(1.0)
        check(b"\x1dV" not in printer.data[before:], "cut suppressed when feature is off")

        # 11. the start-up slip was printed and carries the address
        start_slip = printer.data[:20000]
        check(b"BonBridge" in start_slip, "startup slip printed")
        check(b"127.0.0.1" in start_slip, "startup slip contains the IP address")
        check(str(RAW_PORT).encode() in start_slip, "startup slip contains the port")

        # 12. cash drawer: HIGH is ambiguous, LOW proves a drawer exists
        entry = get_json("/api/printers/theke1")["printer"]
        check(entry["drawer"]["state"] == "open_or_absent", "drawer reported as open or absent")
        check(entry["drawer"]["connected"] is False, "ambiguous drawer is not claimed as connected")
        printer.state.drawer_pin_high = False
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(0.4)
        entry = get_json("/api/printers/theke1")["printer"]
        check(entry["drawer"]["state"] == "connected_closed", "closed drawer detected")
        check(entry["drawer"]["connected"] is True, "closed drawer counts as connected")
        printer.state.drawer_pin_high = True
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(0.4)
        entry = get_json("/api/printers/theke1")["printer"]
        check(
            entry["drawer"]["state"] == "connected_open",
            "remembered drawer upgrades the ambiguous reading",
        )

        # 13. paper-low warning slip, printed once
        get_json(
            "/api/printers/theke1",
            method="PATCH",
            payload={"options": {"paper_low_warning": True}},
        )
        time.sleep(1.5)
        printer.state.paper_near_end = True
        before = len(printer.data)
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(1.2)
        slip = printer.data[before:]
        check(escpos.encode_text("PAPIER FAST LEER", "cp1252") in slip, "paper-low slip printed")
        before = len(printer.data)
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(1.0)
        check(
            escpos.encode_text("PAPIER FAST LEER", "cp1252") not in printer.data[before:],
            "paper-low slip is not repeated",
        )
        printer.state.paper_near_end = False
        get_json("/api/printers/theke1/refresh", method="POST")
        time.sleep(0.4)

        # 14. compose: preview first, then print
        spec = {
            "elements": [
                {"type": "text", "text": "Tisch 7", "align": "center", "bold": True, "size": "double"},
                {"type": "divider"},
                {"type": "kv", "left": "2x Cola", "right": "7,00"},
                {"type": "kv", "left": "Summe", "right": "15,40"},
                {"type": "qr", "data": "https://example.invalid/"},
            ],
            "cut": True,
        }
        result = get_json(
            "/api/printers/theke1/compose", method="POST", payload={"spec": spec, "print": False}
        )
        check(result["columns"] == 56, "preview uses the detected line width")
        texts = [line["text"] for line in result["preview"]]
        check(any("Tisch 7" in text for text in texts), "preview contains the heading")
        check(
            any(line["double"] and line["align"] == "center" for line in result["preview"]),
            "preview carries the formatting attributes",
        )
        kv_lines = [
            text for text in texts if text.startswith("2x Cola") and text.rstrip().endswith("7,00")
        ]
        check(bool(kv_lines), "preview contains the price line")
        check(
            bool(kv_lines) and len(kv_lines[0]) == result["columns"],
            f"price line is padded to the full width ({result['columns']})",
        )
        check(
            bool(kv_lines) and kv_lines[0].endswith("7,00") and "  " in kv_lines[0],
            "amount is flush right, padding preserved",
        )
        before = len(printer.data)
        check(len(printer.data) == before, "preview alone prints nothing")
        result = get_json(
            "/api/printers/theke1/compose", method="POST", payload={"spec": spec, "print": True}
        )
        time.sleep(1.2)
        printed = printer.data[before:]
        check(escpos.encode_text("Summe", "cp1252") in printed, "composed receipt printed")
        check(b"\x1d(k" in printed, "composed receipt contains the QR code")

        # 15. discovery: an ENPC probe is logged and answered
        probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe_socket.settimeout(2.0)
        probe = b"EPSONQ" + bytes([0x03, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00])
        probe_socket.sendto(probe, ("127.0.0.1", ENPC_PORT))
        reply = b""
        try:
            reply, _ = probe_socket.recvfrom(1024)
        except socket.timeout:
            pass
        probe_socket.close()
        check(reply.startswith(b"EPSONq"), "ENPC probe answered with the reply magic")
        discovery = get_json("/api/discovery")["discovery"]["enpc"]
        check(discovery["requests"] >= 1, "ENPC probe counted")
        check(len(discovery["probes"]) >= 1, "ENPC probe recorded with a hexdump")
        queries = [entry for entry in discovery["probes"] if entry.get("magic") == "EPSONQ"]
        check(bool(queries), "the query is recorded as an ENPC query")
        check("45 50 53 4f 4e 51" in queries[0]["hexdump"], "hexdump shows the magic")
        check(queries[0]["answered"] is True, "probe log records that it was answered")
        check(
            len(discovery["probes"]) == len(queries),
            "no self-answer loop: only real probes are logged",
        )

        # 16. documentation is served as HTML
        with urllib.request.urlopen(f"http://127.0.0.1:{WEB_PORT}/docs?lang=de", timeout=5) as response:
            index_html = response.read().decode()
        check("Dokumentation" in index_html, "documentation index rendered")
        with urllib.request.urlopen(
            f"http://127.0.0.1:{WEB_PORT}/docs/de/07-ausdruckgruppen.md", timeout=5
        ) as response:
            doc_html = response.read().decode()
        check("<h1" in doc_html and "<table" in doc_html, "documentation page rendered as HTML")
        check("docnav" in doc_html, "documentation page has navigation")
        with urllib.request.urlopen(f"http://127.0.0.1:{WEB_PORT}/docs-img/wiring-usb.svg", timeout=5) as response:
            check(response.status == 200, "documentation image served")

        # 8b. network watchdog over the API
        network = get_json("/api/network")["network"]
        check("interfaces" in network, "network state served over the API")
        checked = get_json("/api/network/check", method="POST")
        check(checked.get("ok"), "on-demand network check runs")
        overview = get_json("/api/overview")
        check("network" in overview, "overview carries the network state")
        before = len(printer.data)
        get_json("/api/printers/theke1/network-test", method="POST", payload={"online": False})
        time.sleep(1.5)
        check(len(printer.data) > before, "the outage slip can be printed on demand")

        # 8c. printing an image
        support = get_json("/api/image/support")["support"]
        check("available" in support, "image support is reported")
        if support["available"]:
            from PIL import Image as PILImage

            buffer = io.BytesIO()
            PILImage.new("L", (120, 60), 128).save(buffer, format="PNG")
            request = urllib.request.Request(
                f"http://127.0.0.1:{WEB_PORT}/api/printers/theke1/image?scale=80",
                data=buffer.getvalue(),
                method="POST",
            )
            request.add_header("Content-Type", "application/octet-stream")
            with urllib.request.urlopen(request, timeout=15) as response:
                prepared = json.loads(response.read())
            check(prepared.get("ok"), "an uploaded image is rasterised")
            check(prepared["preview_png"].startswith("data:image/png"), "preview returned")
            before = len(printer.data)
            printed = get_json(
                "/api/printers/theke1/image/print",
                method="POST",
                payload={"token": prepared["token"]},
            )
            check(printed.get("ok"), "the previewed image is printed")
            time.sleep(1.5)
            check(len(printer.data) > before, "raster data reached the printer")

            # A PDF has to be refused with a useful message, not a stack trace.
            request = urllib.request.Request(
                f"http://127.0.0.1:{WEB_PORT}/api/printers/theke1/image",
                data=b"%PDF-1.4 fake",
                method="POST",
            )
            request.add_header("Content-Type", "application/octet-stream")
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    refused = json.loads(response.read())
                check(
                    refused.get("ok") is False and "PDF" in refused.get("error", ""),
                    "a PDF is refused with an explanation",
                )
            except urllib.error.HTTPError:
                check(False, "a PDF is refused with an explanation")


        # 9. spooling: printer unreachable -> job is kept, then delivered
        printer.stop()
        time.sleep(0.3)
        with socket.create_connection(("127.0.0.1", RAW_PORT), timeout=5) as sock:
            sock.sendall(b"\x1b@Nachzuegler\n\n\n")
        time.sleep(2.0)
        entry = get_json("/api/printers/theke1")["printer"]
        check(entry["spooled"] >= 1 or entry["queued"] >= 1, "job spooled while printer offline")

        printer2 = MockPrinter("127.0.0.1", PRINTER_PORT).start()
        time.sleep(8.0)
        check(b"Nachzuegler" in printer2.data, "spooled job delivered after reconnect")
        printer2.stop()

        # 10. integration info and support report
        integration = get_json("/api/printers/theke1/integration")["integration"]
        check(integration["port"] == RAW_PORT, "integration info reports the port")
        check(integration["recommendation"]["columns"] == 56, "integration info reports line width")
        report = get_json("/api/report")
        check("BonBridge support report" in report, "support report generated")
        check("Printer 'Theke 1'" in report, "support report contains the printer")

        # 17. static assets
        with urllib.request.urlopen(f"http://127.0.0.1:{WEB_PORT}/", timeout=5) as response:
            html = response.read().decode()
        check("BonBridge" in html and "app.js" in html, "web interface served")

        # 11. updates
        update = get_json("/api/update")["update"]
        check(update["current"] == overview["version"], "update card knows the running version")
        check(update["allow_web"] is True, "web updates are allowed by default")
        log = get_json("/api/update/log")
        check(log.get("ok"), "update log endpoint answers")

        # A file that is not a release must be refused before anything happens.
        request = urllib.request.Request(
            f"http://127.0.0.1:{WEB_PORT}/api/update/upload?name=evil.tar.gz",
            data=b"this is not a tar file",
            method="POST",
        )
        request.add_header("Content-Type", "application/octet-stream")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read())
            check(payload.get("ok") is False, "a bogus update file is rejected")
        except urllib.error.HTTPError as exc:
            check(exc.code in (400, 500), "a bogus update file is rejected")

        # Turning the switch off must actually close the door.
        get_json("/api/config", method="PUT", payload={"update": {"allow_web": False}})
        request = urllib.request.Request(
            f"http://127.0.0.1:{WEB_PORT}/api/update/install",
            data=json.dumps({"source": "online"}).encode(),
            method="POST",
        )
        request.add_header("Content-Type", "application/json")
        try:
            urllib.request.urlopen(request, timeout=10)
            check(False, "web updates are refused when switched off")
        except urllib.error.HTTPError as exc:
            check(exc.code == 403, f"web updates are refused when switched off (HTTP {exc.code})")
        get_json("/api/config", method="PUT", payload={"update": {"allow_web": True}})


    finally:
        web.stop()
        app.stop()
        try:
            printer.stop()
        except Exception:  # noqa: BLE001
            pass

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
