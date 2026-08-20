"""Command line entry point: ``python3 -m bonbridge``."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, List, Optional

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

    update = subparsers.add_parser("update", help="check for a new version and install it")
    update.add_argument("--check", action="store_true", help="only check, do not install")
    update.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    update.add_argument("--file", default=None, help="install from a local archive (offline)")
    update.add_argument("--repo", default=None, help="GitHub repository (owner/name)")
    update.add_argument(
        "--rollback", action="store_true", help="restore the installation from before the last update"
    )
    update.add_argument("--list-backups", action="store_true", help="show available backups")
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


def _confirm(question: str) -> bool:
    try:
        answer = input(f"{question} [j/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("j", "ja", "y", "yes")


def command_update(args: Any, config: Any) -> int:  # noqa: C901 - a linear script reads better
    """``bonbridge update`` - check, ask once, install with live output."""
    import os
    from pathlib import Path

    from . import updater

    settings = config.data.get("update") or {}
    repository = args.repo or str(settings.get("repository") or "loe17/Bonbridge")

    print(f"BonBridge {__version__}")
    print("=" * 60)

    if args.list_backups:
        backups = updater.list_backups()
        if not backups:
            print("No backups yet.")
            return 0
        for entry in backups:
            import time as _time

            when = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(entry["time"]))
            print(f"  {entry['file']}   {entry['size'] // 1024} kB   {when}")
        return 0

    if args.rollback:
        if os.geteuid() != 0:
            print("Rollback needs root:  sudo bonbridge update --rollback", file=sys.stderr)
            return 1
        result = updater.rollback()
        if not result.get("ok"):
            print(f"Rollback not possible: {result.get('error')}", file=sys.stderr)
            return 1
        print(f"Restoring {result['backup']} (version {result.get('version') or '?'})")
        if not (args.yes or _confirm("Wirklich zurueckrollen? / Really roll back?")):
            print("Cancelled.")
            return 1
        return updater.run_foreground(Path(result["source"]), result.get("version") or "rollback")

    # ---- offline: install from a file -------------------------------------
    if args.file:
        archive = Path(args.file).expanduser()
        if not archive.is_file():
            print(f"File not found: {archive}", file=sys.stderr)
            return 1
        if os.geteuid() != 0:
            print("Installing needs root:  sudo bonbridge update --file ...", file=sys.stderr)
            return 1
        try:
            source = updater.prepare_from_file(archive, echo=print)
        except Exception as exc:  # noqa: BLE001
            print(f"The archive cannot be used: {exc}", file=sys.stderr)
            return 1
        version = updater.archive_version(source) or "?"
        print(f"Archive contains version {version} (installed: {__version__})")
        if not updater.is_newer(version) and version != "?":
            print("This is not newer than what is installed.")
        if not (args.yes or _confirm(f"Version {version} jetzt installieren? / Install now?")):
            print("Cancelled.")
            return 1
        updater.backup()
        return updater.run_foreground(source, version)

    # ---- online: check GitHub ---------------------------------------------
    print(f"Checking https://github.com/{repository} ...")
    info = updater.check(repository)
    if not info.get("ok"):
        print(f"Check failed: {info.get('error')}", file=sys.stderr)
        print("Offline? Then download the release on another machine and use:")
        print("  sudo bonbridge update --file bonbridge-x.y.z.tar.gz")
        return 1

    print(f"  installed: {info['current']}")
    print(f"  available: {info['latest']}  ({info.get('name') or ''})")
    if not info.get("update_available"):
        print("\nAlready up to date.")
        return 0

    notes = (info.get("notes") or "").strip()
    if notes:
        print("\nRelease notes")
        print("-" * 60)
        for line in notes.splitlines()[:40]:
            print(f"  {line}")
        print("-" * 60)
    if info.get("html_url"):
        print(f"  {info['html_url']}")

    if args.check:
        return 0
    if os.geteuid() != 0:
        print("\nInstalling needs root:  sudo bonbridge update", file=sys.stderr)
        return 1

    print()
    print("The update replaces the program files in /opt/bonbridge and restarts")
    print("the service.  The configuration in /etc/bonbridge is kept.")
    print("A backup of the current installation is written first.")
    if not (args.yes or _confirm(f"Version {info['latest']} jetzt installieren? / Install now?")):
        print("Cancelled.")
        return 1

    try:
        source = updater.prepare_from_release(info, echo=print)
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1
    backup_file = updater.backup()
    if backup_file:
        print(f"Backup: {backup_file}")
    code = updater.run_foreground(source, info["latest"])
    updater.cleanup_work_dirs()
    if code == 0:
        print(f"\nBonBridge {info['latest']} installed.")
    else:
        print(f"\nUpdate failed (exit code {code}).", file=sys.stderr)
        print("Roll back with:  sudo bonbridge update --rollback", file=sys.stderr)
    return code


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

    if args.command == "update":
        setup_logging(args.log_level or "WARNING", to_file=False)
        return command_update(args, config)

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
