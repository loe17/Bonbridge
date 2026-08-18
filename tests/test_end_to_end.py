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

from bonbridge import escpos, paths  # noqa: E402
from bonbridge.config import Config  # noqa: E402
from bonbridge.daemon import BonBridge  # noqa: E402
from bonbridge.web.server import WebServer  # noqa: E402
from mock_printer import MockPrinter  # noqa: E402

RAW_PORT = 19100
WEB_PORT = 18080
PRINTER_PORT = 19200

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


def main() -> int:
    printer = MockPrinter("127.0.0.1", PRINTER_PORT).start()
    print(f"mock printer on 127.0.0.1:{PRINTER_PORT}")

    config = Config(
        {
            "web": {"bind": "127.0.0.1", "port": WEB_PORT},
            "raw": {"port": RAW_PORT},
            "discovery": {"mdns": False, "enpc": False},
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
        get_json(f"/api/printers/theke1/refresh", method="POST")
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
        check(
            any("Paper end" in message for message in entry["status_messages"]),
            "paper end message present",
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

        # 11. static assets
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
