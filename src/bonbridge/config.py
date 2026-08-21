"""Configuration handling.

The configuration is a single YAML file (``/etc/bonbridge/config.yaml``).
It is read at start-up and can be rewritten by the web interface.  Every
value has a defined default so that a missing or partial file still yields a
working daemon.

PyYAML is used when available (``apt install python3-yaml``); if it is not,
BonBridge falls back to a JSON file with the same schema so the daemon never
becomes unusable because of a missing dependency.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import paths

log = logging.getLogger(__name__)

try:  # pragma: no cover - depends on the host
    import yaml

    HAVE_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    HAVE_YAML = False


# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------

#: OrderAssist (and most other POS apps) address a printer as ``<ip>:9100``
#: with no way to change the port.  9100 is therefore the default and should
#: only be changed for testing.
DEFAULT_RAW_PORT = 9100

DEFAULT_PRINTER_OPTIONS: Dict[str, Any] = {
    # Print a status receipt (IP address, port, POS settings, QR code) when the
    # daemon starts.  On by default because the device usually has no screen
    # and the printed slip is the fastest way to learn the IP address.
    "startup_report": True,
    # Print a warning slip when the printer reports "paper near end".
    # Off by default so it cannot surprise anyone during service.
    "paper_low_warning": False,
    # Print a slip on this printer when the *device* loses or regains its
    # network connection.  The USB link to the printer is unaffected by a
    # network outage, so the printer is the only thing left that can explain
    # why the POS application stopped printing.
    "network_alert": True,
    # Append a paper cut after every job.  Most POS apps send their own cut
    # command, so this is off by default.
    "cut_after_job": False,
    "cut_mode": "partial",  # partial | full
    # Feed n lines before cutting / at the end of the job.
    "feed_lines_after_job": 0,
    # Fire the cash drawer pulse after every job.
    "open_drawer_after_job": False,
    "drawer_pin": 0,  # 0 = pin 2, 1 = pin 5
    # Poll DLE EOT status in the background so the web interface can show
    # paper / cover / error state.
    "status_polling": True,
    "status_interval": 10.0,
    # Enable Automatic Status Back so the printer reports changes on its own.
    "asb": False,
    # Force a code page before each job (``None`` = leave the stream alone).
    "force_codepage": None,
    # Reset the printer (ESC @) before each job.
    "reset_before_job": False,
}

DEFAULT_QUEUE_OPTIONS: Dict[str, Any] = {
    "retry_seconds": 5.0,
    "max_retries": 0,  # 0 = retry forever
    "spool_on_error": True,
    "max_spool_files": 200,
    "job_timeout": 120.0,
}

#: Feature switches exposed in the web interface.  ``None`` means "use the
#: automatically detected value"; ``True``/``False`` is an explicit override.
FEATURE_KEYS = (
    "cutter",
    "cashdrawer",
    "buzzer",
    "barcode",
    "qrcode",
    "pdf417",
    "graphics",
    "nv_images",
    "status_readback",
)

DEFAULTS: Dict[str, Any] = {
    "version": 1,
    "hostname_label": "",  # free text shown in the web interface
    "web": {
        "bind": "0.0.0.0",
        "port": 8080,
        "language": "de",  # de | en
    },
    "raw": {
        "port": DEFAULT_RAW_PORT,
        "max_connections": 8,
    },
    #: Being found automatically is not one protocol but four.  A real Epson
    #: interface board (UB-E04) answers ENPC, SNMP, mDNS and LPD, and different
    #: apps use different ones - so BonBridge answers all of them and records
    #: every probe, which turns "the printer is not found" into a measurement.
    "discovery": {
        "mdns": True,
        # Epson ENPC responder (UDP 3289).  This is what the Epson ePOS SDK
        # broadcasts.  Epson does not publish the reply format, so the reply is
        # best effort - see discovery.py for the variants.
        "enpc": True,
        "enpc_port": 3289,
        # Which ENPC reply layout to send.  "cycle" answers each retry of the
        # searching app with the next candidate, so one search run tries them
        # all; the probe log names the one that was used.  A candidate id
        # (e.g. "device") pins that layout once it is known to work.
        "enpc_reply": "cycle",
        # SNMP v1 on UDP 161 with community "public", exactly as the UB-E04
        # does.  Sweeping a subnet with one SNMP query is the most common way
        # printer discovery is implemented.
        "snmp": True,
        "snmp_port": 161,
        "snmp_community": "public",
        # LPD/LPR on TCP 515.  Answers queue probes and accepts print jobs.
        "lpd": True,
        "lpd_port": 515,
        # Passive listeners that only record who knocks - IPP, ePOS, SSDP.
        "watch_ports": True,
        "watch_tcp": [631, 8008],
        "watch_udp": [1900],
        # What BonBridge calls itself in ENPC, SNMP and mDNS.  Apps that filter
        # for Epson devices match on these, so "auto" uses the detected model
        # and falls back to a TM model name when nothing was detected.
        "advertise_vendor": "EPSON",
        "advertise_model": "auto",
        "advertise_fallback": "TM-T88V",
        # Log every discovery probe with a hexdump so the reply format can be
        # verified against a real app.
        "log_probes": True,
    },
    #: Watches the device's own network connection (see netwatch.py).  Which
    #: printers report an outage is decided per printer via the
    #: ``network_alert`` option.
    "network_watch": {
        "enabled": True,
        # Seconds between checks.  Reading sysfs is cheap; 60 s is a compromise
        # between noticing quickly and not writing a log line every second.
        "interval": 60.0,
        "print_on_loss": True,
        "print_on_restore": True,
        # Additionally ping the default gateway.  Catches "connected but the
        # router is dead", costs one subprocess per check - hence off.
        "gateway_check": False,
        # How many consecutive checks a changed state has to survive before it
        # counts.  2 keeps a short Wi-Fi roam from producing a slip.
        "confirmations": 2,
    },
    #: Software updates from GitHub (see updater.py).
    "update": {
        "repository": "loe17/Bonbridge",
        # Only published releases/tags are offered, never the moving branch.
        "channel": "release",
        "check_on_start": True,
        "check_interval_hours": 24,
        # Whether the web interface may install updates.  The interface has no
        # password, so this is genuinely a security switch: turning it off
        # leaves "bonbridge update" over SSH as the only way in.
        "allow_web": True,
    },
    "logging": {
        "level": "INFO",
        "keep_job_dumps": 20,
    },
    "printers": [],
}

DEFAULT_PRINTER: Dict[str, Any] = {
    "id": "printer1",
    "name": "Drucker 1",
    "enabled": True,
    # Which local IP address the RAW listener binds to.  ``0.0.0.0`` serves
    # every address of the machine.  For several print groups on one device
    # give each printer its own IP alias here (see docs).
    "bind": "0.0.0.0",
    "transport": {"type": "auto"},
    "profile": "auto",
    "features": {key: None for key in FEATURE_KEYS},
    "options": dict(DEFAULT_PRINTER_OPTIONS),
    "queue": dict(DEFAULT_QUEUE_OPTIONS),
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def normalise_printer(raw: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    """Fill a printer entry with defaults and sanitise obvious mistakes."""
    printer = _deep_merge(DEFAULT_PRINTER, raw or {})

    if not printer.get("id"):
        printer["id"] = f"printer{index + 1}"
    printer["id"] = str(printer["id"]).strip().replace(" ", "-")
    if not printer.get("name"):
        printer["name"] = printer["id"]

    transport = printer.get("transport") or {}
    if not isinstance(transport, dict):
        transport = {"type": "auto"}
    transport.setdefault("type", "auto")
    printer["transport"] = transport

    features = printer.get("features") or {}
    printer["features"] = {key: features.get(key) for key in FEATURE_KEYS}

    printer["options"] = _deep_merge(DEFAULT_PRINTER_OPTIONS, printer.get("options") or {})
    printer["queue"] = _deep_merge(DEFAULT_QUEUE_OPTIONS, printer.get("queue") or {})
    return printer


class Config:
    """In-memory view of the configuration file."""

    def __init__(self, data: Optional[Dict[str, Any]] = None, path: Optional[Path] = None):
        self.path = Path(path) if path else paths.CONFIG_FILE
        self.data = _deep_merge(DEFAULTS, data or {})
        self.data["printers"] = [
            normalise_printer(entry, i) for i, entry in enumerate(self.data.get("printers") or [])
        ]
        self._dedupe_ids()

    # -- loading / saving --------------------------------------------------

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        path = Path(path) if path else paths.CONFIG_FILE
        if not path.exists():
            log.info("No configuration at %s - starting with defaults", path)
            return cls(path=path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.error("Cannot read %s: %s - using defaults", path, exc)
            return cls(path=path)

        data: Any = None
        if HAVE_YAML:
            try:
                data = yaml.safe_load(text)
            except Exception as exc:  # noqa: BLE001 - config errors must not crash
                log.error("Invalid YAML in %s: %s", path, exc)
        if data is None:
            try:
                data = json.loads(text)
            except Exception:  # noqa: BLE001
                pass
        if not isinstance(data, dict):
            log.error("Configuration %s is not a mapping - using defaults", path)
            data = {}
        return cls(data, path=path)

    def save(self, path: Optional[Path] = None) -> Path:
        """Atomically write the configuration back to disk."""
        target = Path(path) if path else self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if HAVE_YAML:
            text = yaml.safe_dump(self.data, allow_unicode=True, sort_keys=False, indent=2)
            header = (
                "# BonBridge configuration\n"
                "# Documentation: docs/de/05-weboberflaeche.md\n"
                "# Changes take effect after: systemctl restart bonbridge\n"
            )
            text = header + text
        else:  # pragma: no cover - only without PyYAML
            text = json.dumps(self.data, indent=2, ensure_ascii=False)

        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".config-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(tmp_name, target)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        log.info("Configuration written to %s", target)
        return target

    # -- accessors ---------------------------------------------------------

    @property
    def printers(self) -> List[Dict[str, Any]]:
        return self.data["printers"]

    def printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.printers:
            if entry["id"] == printer_id:
                return entry
        return None

    def add_printer(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        printer = normalise_printer(raw, len(self.printers))
        self.printers.append(printer)
        self._dedupe_ids()
        return printer

    def remove_printer(self, printer_id: str) -> bool:
        before = len(self.printers)
        self.data["printers"] = [p for p in self.printers if p["id"] != printer_id]
        return len(self.printers) != before

    def update_printer(self, printer_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for index, entry in enumerate(self.printers):
            if entry["id"] == printer_id:
                merged = _deep_merge(entry, patch or {})
                self.printers[index] = normalise_printer(merged, index)
                self._dedupe_ids()
                return self.printers[index]
        return None

    def _dedupe_ids(self) -> None:
        seen = set()  # type: ignore[var-annotated]
        for index, entry in enumerate(self.printers):
            candidate = entry["id"]
            suffix = 2
            while candidate in seen:
                candidate = f"{entry['id']}-{suffix}"
                suffix += 1
            entry["id"] = candidate
            seen.add(candidate)

    def as_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self.data)
