"""Command line entry point: ``python3 -m bonbridge``."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from . import __version__, paths
from .config import Config
from .daemon import BonBridge
from .web.server import WebServer


def setup_logging(level: str = "INFO", to_file: bool = True) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    if to_file:
        try:
            paths.LOG_DIR.mkdir(parents=True, exist_ok=True)
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                paths.LOG_DIR / "bonbridge.log", maxBytes=1_000_000, backupCount=3
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bonbridge",
        description="Expose USB / serial ESC-POS receipt printers as network printers on port 9100.",
    )
    parser.add_argument("--version", action="version", version=f"BonBridge {__version__}")
    parser.add_argument("--config", help="path to config.yaml", default=None)
    parser.add_argument("--log-level", default=None, help="DEBUG, INFO, WARNING, ERROR")
    parser.add_argument("--no-log-file", action="store_true", help="log to stderr only")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="run the daemon (default)")
    subparsers.add_parser("scan", help="list printers that can be used and exit")
    subparsers.add_parser("report", help="print the support report and exit")
    test = subparsers.add_parser("test", help="send a test page and exit")
    test.add_argument("--printer", default=None, help="printer id (default: the first one)")
    test.add_argument("--kind", default="standard", choices=["standard", "features", "minimal"])
    return parser


def command_scan() -> int:
    from .transports import runtime_report, scan_devices

    print("Available transports:")
    for name, info in runtime_report().items():
        mark = "yes" if info["available"] else "no "
        print(f"  [{mark}] {name:<8} {info['hint']}")
    print("\nDetected devices:")
    devices = scan_devices()
    if not devices:
        print("  (none - is the printer switched on and connected? It needs its own 24 V supply)")
    for device in devices:
        print(f"  {device.get('transport'):<7} {device.get('label')}")
        for key in ("vendor_id_hex", "product_id_hex", "serial", "ieee1284_id", "device"):
            if device.get(key):
                print(f"          {key}: {device[key]}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config:
        import os
        from pathlib import Path

        os.environ["BONBRIDGE_CONFIG"] = args.config
        paths.CONFIG_FILE = Path(args.config).expanduser()

    if args.command == "scan":
        setup_logging(args.log_level or "WARNING", to_file=False)
        return command_scan()

    config = Config.load(paths.CONFIG_FILE)
    level = args.log_level or str((config.data.get("logging") or {}).get("level") or "INFO")
    setup_logging(level, to_file=not args.no_log_file)

    app = BonBridge(config)

    if args.command == "report":
        app._ensure_default_printer()  # noqa: SLF001 - CLI convenience
        app._start_printers()  # noqa: SLF001
        import time

        time.sleep(2.0)  # give the workers a moment to connect and identify
        print(app.support_report())
        app.stop()
        return 0

    if args.command == "test":
        app.start()
        import time

        time.sleep(2.0)
        printer_id = args.printer or (next(iter(app.printers), None))
        if not printer_id:
            print("No printer configured.", file=sys.stderr)
            app.stop()
            return 1
        result = app.test_print(printer_id, args.kind)
        print(result)
        time.sleep(3.0)
        app.stop()
        return 0 if result.get("ok") else 1

    # default: run the daemon
    app.install_signal_handlers()
    app.start()

    web_config = config.data.get("web") or {}
    web = WebServer(
        app,
        bind=str(web_config.get("bind") or "0.0.0.0"),
        port=int(web_config.get("port") or 8080),
    )
    app.web_server = web
    web.start()

    try:
        app.wait()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        web.stop()
        app.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
