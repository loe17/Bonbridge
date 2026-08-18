"""Health checks - every warning has to say *why*.

A traffic light that turns yellow without an explanation is worse than no
traffic light at all.  This module produces a list of individual checks, each
with its own level, a short title and a detail line in German and English, so
the web interface can show exactly what is wrong and what to do about it.

Device checks cover the things that actually bite on a Raspberry Pi in a
kitchen: under-voltage from a weak power supply, thermal throttling, a full SD
card, and missing Python bindings for USB.  Printer checks wrap the ESC/POS
status plus the state of the network listener.

References
----------
* Raspberry Pi throttling bits, ``vcgencmd get_throttled``
  https://www.raspberrypi.com/documentation/computers/os.html
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from . import sysinfo

log = logging.getLogger(__name__)

LEVEL_ORDER = {"ok": 0, "info": 0, "warn": 1, "unknown": 1, "offline": 2, "error": 3}

#: Raspberry Pi ``get_throttled`` bit meanings.
THROTTLE_BITS = {
    0: ("undervoltage_now", "error"),
    1: ("freq_capped_now", "warn"),
    2: ("throttled_now", "warn"),
    3: ("soft_temp_limit_now", "warn"),
    16: ("undervoltage_past", "warn"),
    17: ("freq_capped_past", "info"),
    18: ("throttled_past", "info"),
    19: ("soft_temp_limit_past", "info"),
}

THROTTLE_TEXT = {
    "undervoltage_now": (
        "Unterspannung! Netzteil oder USB-Kabel zu schwach",
        "Under-voltage right now - power supply or cable too weak",
    ),
    "freq_capped_now": ("Taktfrequenz gerade begrenzt", "CPU frequency capped right now"),
    "throttled_now": ("Gerät wird gerade gedrosselt", "Device is being throttled right now"),
    "soft_temp_limit_now": ("Temperaturgrenze gerade aktiv", "Soft temperature limit active"),
    "undervoltage_past": (
        "Seit dem Start gab es Unterspannung - Netzteil prüfen",
        "Under-voltage occurred since boot - check the power supply",
    ),
    "freq_capped_past": ("Taktfrequenz war zeitweise begrenzt", "CPU frequency was capped earlier"),
    "throttled_past": ("Gerät wurde zeitweise gedrosselt", "Device was throttled earlier"),
    "soft_temp_limit_past": (
        "Temperaturgrenze war zeitweise aktiv",
        "Soft temperature limit was active earlier",
    ),
}


def _check(
    check_id: str,
    level: str,
    title_de: str,
    title_en: str,
    detail_de: str = "",
    detail_en: str = "",
    value: Any = None,
) -> Dict[str, Any]:
    return {
        "id": check_id,
        "level": level,
        "title_de": title_de,
        "title_en": title_en,
        "detail_de": detail_de,
        "detail_en": detail_en,
        "value": value,
    }


def worst_level(levels: List[str]) -> str:
    worst = "ok"
    for level in levels:
        if LEVEL_ORDER.get(level, 1) > LEVEL_ORDER.get(worst, 0):
            worst = level
    return worst


# --------------------------------------------------------------------------
# Raspberry Pi throttling
# --------------------------------------------------------------------------


def read_throttled() -> Optional[int]:
    """Read the Raspberry Pi throttling bitmask, or ``None`` on other boards."""
    for path in (
        "/sys/devices/platform/soc/soc:firmware/get_throttled",
        "/sys/devices/platform/soc:firmware/get_throttled",
    ):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return int(handle.read().strip(), 16)
        except (OSError, ValueError):
            continue
    if shutil.which("vcgencmd"):
        try:
            result = subprocess.run(  # noqa: S603 - fixed command
                ["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=4, check=False
            )
            text = (result.stdout or "").strip()
            if "=" in text:
                return int(text.split("=", 1)[1], 16)
        except Exception as exc:  # noqa: BLE001
            log.debug("vcgencmd failed: %s", exc)
    return None


def throttle_checks() -> List[Dict[str, Any]]:
    mask = read_throttled()
    if mask is None:
        return []
    if mask == 0:
        return [
            _check(
                "power",
                "ok",
                "Stromversorgung in Ordnung",
                "Power supply healthy",
                "Keine Unterspannung und keine Drosselung seit dem Start.",
                "No under-voltage and no throttling since boot.",
                value="0x0",
            )
        ]
    checks: List[Dict[str, Any]] = []
    for bit, (name, level) in THROTTLE_BITS.items():
        if mask & (1 << bit):
            title_de, title_en = THROTTLE_TEXT[name]
            checks.append(
                _check(
                    f"power_{name}",
                    level,
                    title_de,
                    title_en,
                    "Ein zu schwaches Netzteil oder ein dünnes USB-Kabel ist die häufigste "
                    "Ursache. Beim Raspberry Pi Zero 2 W mindestens 5 V / 2,5 A verwenden, "
                    "beim Pi 4/5 das Original-Netzteil.",
                    "A weak power supply or a thin USB cable is the usual cause. Use at least "
                    "5 V / 2.5 A on a Pi Zero 2 W and the original PSU on a Pi 4/5.",
                    value=f"0x{mask:x}",
                )
            )
    return checks


# --------------------------------------------------------------------------
# Device level
# --------------------------------------------------------------------------


def device_checks(app: Any = None) -> List[Dict[str, Any]]:
    """Everything that is about the box itself, not about a printer."""
    checks: List[Dict[str, Any]] = []
    checks.extend(throttle_checks())

    temperature = sysinfo.cpu_temperature()
    if temperature is not None:
        if temperature >= 80:
            level = "error"
        elif temperature >= 70:
            level = "warn"
        else:
            level = "ok"
        checks.append(
            _check(
                "temperature",
                level,
                f"CPU-Temperatur {temperature:.0f} °C",
                f"CPU temperature {temperature:.0f} °C",
                "Ab etwa 80 °C drosselt der Raspberry Pi. Für bessere Kühlung sorgen oder "
                "das Gehäuse öffnen." if level != "ok" else "Im normalen Bereich.",
                "The Raspberry Pi throttles from about 80 °C. Improve cooling or open the "
                "case." if level != "ok" else "Within the normal range.",
                value=round(temperature, 1),
            )
        )

    disk = sysinfo.disk()
    if disk.get("total"):
        free_mb = disk["free"] / (1024 * 1024)
        percent_free = 100.0 * disk["free"] / disk["total"]
        if free_mb < 50 or percent_free < 3:
            level = "error"
        elif free_mb < 250 or percent_free < 10:
            level = "warn"
        else:
            level = "ok"
        checks.append(
            _check(
                "disk",
                level,
                f"Speicherplatz frei: {free_mb / 1024:.1f} GB ({percent_free:.0f} %)",
                f"Free disk space: {free_mb / 1024:.1f} GB ({percent_free:.0f} %)",
                "Bei vollem Speicher können keine Aufträge mehr zwischengespeichert und keine "
                "Logs mehr geschrieben werden. Logs leeren: journalctl --vacuum-size=20M"
                if level != "ok"
                else "Ausreichend Platz für Zwischenspeicher und Logs.",
                "With a full disk no jobs can be spooled and no logs written. Clear logs with: "
                "journalctl --vacuum-size=20M"
                if level != "ok"
                else "Enough room for the spool and the logs.",
                value=int(disk["free"]),
            )
        )

    memory = sysinfo.memory()
    if memory.get("MemTotal"):
        available = memory.get("MemAvailable", 0)
        percent = 100.0 * available / memory["MemTotal"]
        level = "error" if percent < 5 else ("warn" if percent < 12 else "ok")
        checks.append(
            _check(
                "memory",
                level,
                f"Freier Arbeitsspeicher: {available / (1024 * 1024):.0f} MB ({percent:.0f} %)",
                f"Free memory: {available / (1024 * 1024):.0f} MB ({percent:.0f} %)",
                "Wenig freier Speicher. Auf einem Pi Zero 2 W ist das bei laufendem CUPS "
                "normal, sonst laufende Dienste prüfen."
                if level != "ok"
                else "Ausreichend.",
                "Low free memory. On a Pi Zero 2 W that is normal while CUPS runs, otherwise "
                "check the running services."
                if level != "ok"
                else "Sufficient.",
                value=int(available),
            )
        )

    # Python bindings that the configured transports need.
    try:
        from .transports import runtime_report

        report = runtime_report()
        needed = set()
        if app is not None:
            for entry in getattr(app, "config", None).printers if getattr(app, "config", None) else []:
                needed.add(str((entry.get("transport") or {}).get("type") or "auto"))
        for name in sorted(needed):
            info = report.get(name)
            if info and not info["available"]:
                checks.append(
                    _check(
                        f"transport_{name}",
                        "error",
                        f"Anschlussart '{name}' nicht verfügbar",
                        f"Transport '{name}' unavailable",
                        f"Es fehlt: {info['hint']}. Nachinstallieren und den Dienst neu starten.",
                        f"Missing: {info['hint']}. Install it and restart the service.",
                    )
                )
    except Exception as exc:  # noqa: BLE001
        log.debug("transport health check failed: %s", exc)

    if app is not None and not getattr(app, "printers", {}):
        checks.append(
            _check(
                "no_printers",
                "warn",
                "Kein Drucker eingerichtet",
                "No printer configured",
                "Im Reiter 'Drucker' auf 'Geräte suchen' klicken und einen Drucker übernehmen.",
                "Open the 'Printers' tab, click 'Scan for devices' and assign a printer.",
            )
        )

    if not checks:
        checks.append(
            _check(
                "generic",
                "ok",
                "Keine Auffälligkeiten",
                "Nothing to report",
                "Alle Geräteprüfungen sind unauffällig.",
                "All device checks passed.",
            )
        )
    return checks


# --------------------------------------------------------------------------
# Printer level
# --------------------------------------------------------------------------


def printer_checks(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Turn a printer snapshot into explained checks."""
    from . import escpos

    checks: List[Dict[str, Any]] = []

    if not snapshot.get("enabled", True):
        checks.append(
            _check(
                "disabled",
                "info",
                "Drucker ist deaktiviert",
                "Printer is disabled",
                "Im Reiter 'Drucker' den Haken bei 'Aktiv' setzen.",
                "Tick 'Enabled' in the 'Printers' tab.",
            )
        )
        return checks

    if snapshot.get("connected"):
        checks.append(
            _check(
                "connection",
                "ok",
                f"Verbunden über {snapshot.get('connection') or '-'}",
                f"Connected via {snapshot.get('connection') or '-'}",
                "",
                "",
            )
        )
    else:
        checks.append(
            _check(
                "connection",
                "error",
                "Keine Verbindung zum Drucker",
                "No connection to the printer",
                (snapshot.get("last_error") or "")
                + " — Drucker eingeschaltet? Eigenes 24-V-Netzteil angeschlossen? "
                "Kabel und Anschluss prüfen.",
                (snapshot.get("last_error") or "")
                + " — Is the printer switched on with its own 24 V supply? Check cable and port.",
            )
        )

    listener = snapshot.get("listener") or {}
    if listener.get("listening"):
        checks.append(
            _check(
                "listener",
                "ok",
                f"Netzwerk-Listener aktiv auf {listener.get('bind')}:{listener.get('port')}",
                f"Network listener active on {listener.get('bind')}:{listener.get('port')}",
            )
        )
    else:
        checks.append(
            _check(
                "listener",
                "error",
                "Netzwerk-Listener nicht aktiv",
                "Network listener not active",
                (listener.get("error") or "")
                + " — Wenn hier eine feste IP eingetragen ist, muss diese auf dem Gerät "
                "existieren (IP-Alias, siehe Doku zu Ausdruckgruppen).",
                (listener.get("error") or "")
                + " — If a fixed IP is configured it has to exist on the device (IP alias, see "
                "the print groups documentation).",
            )
        )

    level = snapshot.get("status_level") or "unknown"
    for key in snapshot.get("status_messages") or []:
        entry_level = {
            "ok": "ok",
            "no_status": "info",
            "paper_near_end": "warn",
            "printer_offline": "warn",
        }.get(key, "error" if level == "error" else level)
        detail_de, detail_en = STATUS_ADVICE.get(key, ("", ""))
        checks.append(
            _check(
                f"status_{key}",
                entry_level,
                escpos.status_text(key, "de"),
                escpos.status_text(key, "en"),
                detail_de,
                detail_en,
            )
        )

    if snapshot.get("spooled"):
        checks.append(
            _check(
                "spool",
                "warn",
                f"{snapshot['spooled']} Auftrag/Aufträge zwischengespeichert",
                f"{snapshot['spooled']} job(s) spooled",
                "Diese Aufträge konnten noch nicht gedruckt werden und werden automatisch "
                "wiederholt. Unter 'Diagnose' lassen sie sich verwerfen.",
                "These jobs could not be printed yet and are retried automatically. They can be "
                "discarded under 'Diagnostics'.",
            )
        )

    if snapshot.get("jobs_failed"):
        checks.append(
            _check(
                "failures",
                "info",
                f"{snapshot['jobs_failed']} fehlgeschlagene Zustellversuche seit dem Start",
                f"{snapshot['jobs_failed']} failed delivery attempts since start",
                "Einzelne Fehlversuche sind normal, wenn der Drucker zwischendurch aus war.",
                "Occasional failures are normal if the printer was switched off in between.",
            )
        )

    return checks


STATUS_ADVICE = {
    "paper_near_end": (
        "Papierrolle bald wechseln. Eine Warnung auf dem Bon lässt sich pro Drucker "
        "unter 'Drucker' aktivieren.",
        "Replace the paper roll soon. A printed warning can be enabled per printer under "
        "'Printers'.",
    ),
    "paper_end": (
        "Papier einlegen. Eingehende Aufträge werden so lange zwischengespeichert und "
        "danach automatisch gedruckt.",
        "Load paper. Incoming jobs are spooled meanwhile and printed automatically afterwards.",
    ),
    "cover_open": (
        "Deckel schließen. Der Drucker nimmt erst danach wieder Daten an.",
        "Close the cover. The printer only accepts data again afterwards.",
    ),
    "autocutter_error": (
        "Papierstau im Schneidwerk: Deckel öffnen, Papierreste entfernen, Drucker aus- und "
        "wieder einschalten.",
        "Paper jam in the cutter: open the cover, remove the paper, power cycle the printer.",
    ),
    "no_status": (
        "Diese Verbindung hat keinen Rückkanal, deshalb kann der Druckerzustand nicht "
        "gelesen werden. Bei USB tritt das nur auf, wenn der Kernel das Gerät nur "
        "schreibend freigibt.",
        "This connection has no return channel, so the printer state cannot be read. On USB "
        "this only happens when the kernel exposes the device write-only.",
    ),
    "printer_offline": (
        "Der Drucker meldet sich als offline. Meist ist der Deckel offen oder das Papier leer.",
        "The printer reports offline. Usually the cover is open or the paper is empty.",
    ),
}


def summary(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Overall level plus the checks that are not ``ok``."""
    levels = [c["level"] for c in checks]
    level = worst_level(levels)
    return {
        "level": level,
        "checks": checks,
        "problems": [c for c in checks if c["level"] not in ("ok", "info")],
    }
