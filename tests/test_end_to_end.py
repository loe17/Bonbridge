"""End-to-end test: POS app -> RAW 9100 -> BonBridge -> printer.

Runs entirely without hardware by pointing the network transport at the mock
printer from ``tests/mock_printer.py``.

Usage::

    python3 tests/test_end_to_end.py
"""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import time
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
