"""Capability engine.

Answers the question "what can the printer that is actually attached do?" in
four steps, from cheap to expensive:

1. **Identity** - USB vendor/product strings, IEEE-1284 device ID, and the
   ESC/POS ``GS I`` printer ID.
2. **Profile lookup** - the vendored escpos-printer-db plus this project's own
   profiles under ``src/bonbridge/profiles/``.
3. **Live status** - ``DLE EOT`` real-time status (paper, cover, errors).
   This only works because every BonBridge transport is bidirectional.
4. **Active probes** - explicit tests triggered from the web interface
   (cutter, cash drawer, buzzer).  They consume paper, so they never run
   automatically.

Every detected feature can be overridden from the web interface; the result
carries the source ("detected", "profile", "override") so the UI can show
where a value came from.

References
----------
* Printer capability data: escpos-printer-db (CC BY 4.0), vendored at
  ``vendor/escpos-printer-db/capabilities.json``
  https://github.com/receipt-print-hq/escpos-printer-db
  Browsable: https://mike42.me/escpos-printer-db/
* ESC/POS ``GS I`` / ``DLE EOT`` semantics: Epson ESC/POS command reference
  https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/index.html
* IEEE 1284 device ID via the Linux ``usblp`` driver (see transports/usblp.py)
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from . import escpos, paths
from .transports.base import BaseTransport, TransportError

log = logging.getLogger(__name__)

try:  # pragma: no cover
    import yaml

    HAVE_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    HAVE_YAML = False


#: Feature keys exposed to the user, mapped to the escpos-printer-db feature
#: flags that imply them.
FEATURE_SOURCES: Dict[str, Tuple[str, ...]] = {
    "cutter": ("paperFullCut", "paperPartCut"),
    "cashdrawer": ("pulseStandard",),
    "buzzer": ("pulseBel",),
    "barcode": ("barcodeA", "barcodeB"),
    "qrcode": ("qrCode",),
    "pdf417": ("pdf417Code",),
    "graphics": ("graphics", "bitImageRaster", "bitImageColumn"),
    "nv_images": ("graphics",),
}

FEATURE_LABELS = {
    "cutter": ("Papierschneider", "Paper cutter"),
    "cashdrawer": ("Kassenlade (Drawer-Kick)", "Cash drawer kick-out"),
    "buzzer": ("Signalton", "Buzzer"),
    "barcode": ("Barcodes", "Barcodes"),
    "qrcode": ("QR-Codes", "QR codes"),
    "pdf417": ("PDF417-Codes", "PDF417 codes"),
    "graphics": ("Bilddruck / Grafik", "Raster graphics"),
    "nv_images": ("NV-Logo (gespeichertes Logo)", "NV logo"),
    "status_readback": ("Statusabfrage (DLE EOT)", "Status read-back (DLE EOT)"),
}

_DB_CACHE: Optional[Dict[str, Any]] = None
_PROFILE_CACHE: Optional[Dict[str, Any]] = None


# --------------------------------------------------------------------------
# Profile database
# --------------------------------------------------------------------------


def load_capability_db() -> Dict[str, Any]:
    """Load the vendored escpos-printer-db (CC-BY-4.0)."""
    global _DB_CACHE
    if _DB_CACHE is not None:
        return _DB_CACHE
    path = paths.VENDOR_DIR / "escpos-printer-db" / "capabilities.json"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            _DB_CACHE = json.load(handle)
    except Exception as exc:  # noqa: BLE001
        log.error("Cannot load capability database %s: %s", path, exc)
        _DB_CACHE = {"profiles": {}, "encodings": {}}
    return _DB_CACHE


def load_local_profiles() -> Dict[str, Any]:
    """Load this project's own profiles (identity hints + defaults)."""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is not None:
        return _PROFILE_CACHE
    profiles: Dict[str, Any] = {}
    directory = paths.PROFILE_DIR
    if directory.is_dir():
        for path in sorted(directory.glob("*.y*ml")):
            try:
                text = path.read_text(encoding="utf-8")
                data = yaml.safe_load(text) if HAVE_YAML else json.loads(text)
                if isinstance(data, dict) and data.get("id"):
                    profiles[data["id"]] = data
            except Exception as exc:  # noqa: BLE001
                log.warning("Skipping profile %s: %s", path, exc)
    _PROFILE_CACHE = profiles
    return profiles


def list_profiles() -> List[Dict[str, Any]]:
    """All profiles that can be chosen in the web interface."""
    db = load_capability_db().get("profiles", {})
    local = load_local_profiles()
    entries: List[Dict[str, Any]] = []
    for name, profile in sorted(db.items()):
        entries.append(
            {
                "id": name,
                "name": profile.get("name") or name,
                "vendor": profile.get("vendor") or "",
                "source": "escpos-printer-db",
                "columns": _columns_from_db(profile),
                "width_mm": (profile.get("media") or {}).get("width", {}).get("mm"),
            }
        )
    for name, profile in sorted(local.items()):
        entries.append(
            {
                "id": name,
                "name": profile.get("name") or name,
                "vendor": profile.get("vendor") or "",
                "source": "bonbridge",
                "columns": (profile.get("fonts") or {}).get("0", {}).get("columns"),
                "width_mm": profile.get("width_mm"),
            }
        )
    return entries


def _columns_from_db(profile: Dict[str, Any]) -> Optional[int]:
    fonts = profile.get("fonts") or {}
    font_a = fonts.get("0") or fonts.get(0) or {}
    return font_a.get("columns")


def get_profile(profile_id: str) -> Dict[str, Any]:
    """Merged view of a profile: escpos-printer-db entry + local additions."""
    db = load_capability_db().get("profiles", {})
    local = load_local_profiles()
    base = dict(db.get(profile_id) or {})
    extra = local.get(profile_id)
    if extra:
        base_from_db = db.get(extra.get("based_on") or "", {})
        merged = dict(base_from_db)
        merged.update(base)
        for key, value in extra.items():
            if key in ("id", "based_on", "usb_products", "usb_ids", "model_ids"):
                continue
            merged[key] = value
        base = merged
    if not base:
        base = dict(db.get("default") or {})
        base["name"] = profile_id
    return base


# --------------------------------------------------------------------------
# Identification
# --------------------------------------------------------------------------


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def match_profile(identity: Dict[str, Any]) -> Tuple[str, str]:
    """Guess the profile id from identity information.

    Returns ``(profile_id, reason)``.
    """
    product = identity.get("product") or ""
    manufacturer = identity.get("manufacturer") or ""
    vendor_id = identity.get("vendor_id")
    product_id = identity.get("product_id")

    # Every string that may carry the model name.  The IEEE-1284 device ID is
    # the important one for /dev/usb/lpN connections: it reads
    # "MFG:EPSON;MDL:TM-T88V;..." and used to be collected but never matched
    # against, so a printer reached through usblp always fell back to the
    # generic profile even though its model was known.
    sources = [manufacturer, product, identity.get("ieee1284_id") or ""]
    for key, value in (identity.get("gs_i") or {}).items():
        if key.endswith("_text") and isinstance(value, str):
            sources.append(value)
    haystack = _normalise(" ".join(part for part in sources if part))

    if not haystack:
        return (
            "generic-80mm",
            "Keine Modellkennung lesbar - Sammelprofil 80 mm / "
            "no model identification readable - generic 80 mm fallback",
        )

    local = load_local_profiles()

    # 1. explicit USB VID:PID mapping from our own profiles
    if vendor_id is not None and product_id is not None:
        needle = f"{int(vendor_id):04x}:{int(product_id):04x}"
        for profile_id, profile in local.items():
            for candidate in profile.get("usb_ids") or []:
                if str(candidate).lower().replace("0x", "") == needle:
                    return profile_id, f"USB-ID {needle}"

    # 2. product string against our own profiles
    for profile_id, profile in local.items():
        for candidate in profile.get("usb_products") or []:
            if _normalise(candidate) and _normalise(candidate) in haystack:
                return profile_id, f"USB-Produktstring / USB product string '{candidate}'"

    # 3. product string against the escpos-printer-db keys (longest match wins)
    db = load_capability_db().get("profiles", {})
    best: Optional[Tuple[int, str]] = None
    for name in db:
        token = _normalise(name)
        if len(token) >= 4 and token in haystack:
            if best is None or len(token) > best[0]:
                best = (len(token), name)
    if best:
        return best[1], (f"Modellname '{best[1]}' im USB-Deskriptor gefunden / "
                         f"model name found in USB descriptor")

    # 4. width heuristics
    seen = ", ".join(part for part in sources if part)[:120]
    if "58" in (product or ""):
        return "generic-58mm", f"Sammelprofil 58 mm / generic 58 mm fallback (gelesen: {seen})"
    return "generic-80mm", f"Sammelprofil 80 mm / generic 80 mm fallback (gelesen: {seen})"


def query_identity(transport: BaseTransport, timeout: float = 1.0) -> Dict[str, Any]:
    """Ask the printer for its ID via ``GS I`` (needs a bidirectional link)."""
    identity: Dict[str, Any] = {"gs_i": {}, "readable": False}
    if not transport.bidirectional:
        return identity
    queries = (("model", escpos.GS_I_MODEL), ("type", escpos.GS_I_TYPE), ("rom", escpos.GS_I_ROM))
    for name, command in queries:
        try:
            transport.drain(0.05)
            transport.write(command)
            time.sleep(0.08)
            data = transport.read(32, timeout)
        except TransportError as exc:
            log.debug("GS I %s failed: %s", name, exc)
            break
        if data:
            identity["readable"] = True
            identity["gs_i"][name] = data.hex()
            printable = data.decode("ascii", "ignore").strip("\x00\r\n ")
            if printable and printable.isprintable() and len(printable) > 2:
                identity["gs_i"][f"{name}_text"] = printable
    return identity


def read_status(transport: BaseTransport, timeout: float = 0.6) -> Dict[str, Any]:
    """Read the four ``DLE EOT`` status groups."""
    result: Dict[str, Any] = {}
    if not transport.bidirectional:
        return result
    for name, (command, decoder) in escpos.STATUS_DECODERS.items():
        try:
            transport.drain(0.02)
            transport.write(command)
            time.sleep(0.05)
            data = transport.read(8, timeout)
        except TransportError as exc:
            log.debug("Status query %s failed: %s", name, exc)
            return result
        if data:
            result[name] = decoder(data[0])
    return result


# --------------------------------------------------------------------------
# Capability assembly
# --------------------------------------------------------------------------


def profile_features(profile: Dict[str, Any]) -> Dict[str, bool]:
    """Translate escpos-printer-db feature flags into BonBridge features."""
    flags = profile.get("features") or {}
    features: Dict[str, bool] = {}
    for key, sources in FEATURE_SOURCES.items():
        features[key] = any(bool(flags.get(flag)) for flag in sources)
    return features


def fonts_of(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    fonts = profile.get("fonts") or {}
    result: List[Dict[str, Any]] = []
    for index in sorted(fonts, key=lambda k: int(k)):
        entry = fonts[index] or {}
        result.append(
            {
                "index": int(index),
                # POS applications usually count fonts from 1 ("font1"/"font2")
                "app_name": f"font{int(index) + 1}",
                "name": entry.get("name") or f"Font {int(index) + 1}",
                "columns": entry.get("columns"),
            }
        )
    return result


def build_capabilities(
    profile_id: str,
    identity: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    status_readback: Optional[bool] = None,
) -> Dict[str, Any]:
    """Merge profile, detection and user overrides into one object."""
    profile = get_profile(profile_id)
    detected = profile_features(profile)
    detected["status_readback"] = bool(status_readback)

    overrides = overrides or {}
    features: Dict[str, Any] = {}
    for key in list(FEATURE_SOURCES) + ["status_readback"]:
        override = overrides.get(key)
        auto = bool(detected.get(key))
        effective = auto if override is None else bool(override)
        label_de, label_en = FEATURE_LABELS.get(key, (key, key))
        features[key] = {
            "detected": auto,
            "override": override,
            "effective": effective,
            "label_de": label_de,
            "label_en": label_en,
        }

    media = profile.get("media") or {}
    width = media.get("width") or {}
    fonts = fonts_of(profile)
    codepages = {str(k): v for k, v in (profile.get("codePages") or {}).items()}

    return {
        "profile_id": profile_id,
        "profile_name": profile.get("name") or profile_id,
        "vendor": profile.get("vendor") or "",
        "width_mm": width.get("mm") or profile.get("width_mm"),
        "width_px": width.get("pixels"),
        "dpi": media.get("dpi"),
        "fonts": fonts,
        "codepages": codepages,
        "features": features,
        "identity": identity or {},
        "recommendation": recommend_pos_settings(profile_id, profile),
    }


def recommend_pos_settings(profile_id: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Concrete values to type into the POS application.

    OrderAssist asks for *Schriftart* (font1/font2), *Zeichensatz* (code page)
    and *Zeilenbreite* (characters per line) and tells the user to find them
    by trial and error.  BonBridge can simply read them out of the profile.
    """
    profile = profile or get_profile(profile_id)
    fonts = fonts_of(profile)
    codepages = {str(v).lower(): int(k) for k, v in (profile.get("codePages") or {}).items()}

    # Prefer Font B (index 1, "font2" in POS applications).  On an 80 mm Epson
    # that is 56-57 columns, which is what OrderAssist's own example receipt
    # uses and what most receipt layouts are designed for.  Font A is the
    # fallback for printers that only have one font.
    chosen = None
    for font in fonts:
        if font["index"] == 1 and font["columns"]:
            chosen = font
            break
    if chosen is None and fonts:
        chosen = max(fonts, key=lambda f: f["columns"] or 0)

    codepage = "cp1252" if "cp1252" in codepages else ("cp858" if "cp858" in codepages else "cp437")

    return {
        "font": chosen["app_name"] if chosen else "font1",
        "font_name": chosen["name"] if chosen else "Font A",
        "columns": chosen["columns"] if chosen else 42,
        "codepage": codepage,
        "alternatives": [
            {"font": f["app_name"], "name": f["name"], "columns": f["columns"]} for f in fonts
        ],
        "note_de": (
            "Diese Werte in OrderAssist unter 'Drucker korrekt konfigurieren' eintragen. "
            "Die Zeilenbreite stammt aus der Modell-Datenbank: Bricht die Trennlinie auf "
            "der Testseite trotzdem um, den Wert um 1 verringern. Bei abweichendem "
            "Druckbild die Alternativen probieren."
        ),
        "note_en": (
            "Enter these values in the POS application's printer settings. The line "
            "width comes from the model database: if the divider on the test page still "
            "wraps, reduce it by 1. If the layout looks wrong, try the alternatives."
        ),
    }


# --------------------------------------------------------------------------
# Cash drawer
# --------------------------------------------------------------------------

#: What the drawer kick-out connector can and cannot tell us.
#:
#: ESC/POS reports the level of pin 3 of the drawer connector (``DLE EOT 1``
#: bit 2, also ``GS r 2``).  A closed drawer pulls that pin to ground, so:
#:
#:   pin LOW   -> a drawer is definitely connected and currently closed
#:   pin HIGH  -> the drawer is open **or** nothing is connected at all
#:
#: The two HIGH cases are electrically identical, so a single reading cannot
#: distinguish them.  What does distinguish them is history: if the pin has
#: ever been LOW, a drawer exists.  BonBridge therefore remembers that fact
#: across restarts, and offers an active test that fires the pulse and watches
#: whether the pin changes.
DRAWER_UNKNOWN = "unknown"
DRAWER_CONNECTED_CLOSED = "connected_closed"
DRAWER_OPEN_OR_ABSENT = "open_or_absent"
DRAWER_CONNECTED_OPEN = "connected_open"

DRAWER_TEXT = {
    DRAWER_UNKNOWN: (
        "Unbekannt - Status nicht lesbar",
        "Unknown - status not readable",
    ),
    DRAWER_CONNECTED_CLOSED: (
        "Angeschlossen und geschlossen",
        "Connected and closed",
    ),
    DRAWER_CONNECTED_OPEN: (
        "Angeschlossen, gerade offen",
        "Connected, currently open",
    ),
    DRAWER_OPEN_OR_ABSENT: (
        "Offen oder keine angeschlossen",
        "Open or none connected",
    ),
}


def drawer_state(status: Dict[str, Any], seen_connected: bool = False) -> Dict[str, Any]:
    """Interpret the drawer pin from a status reading.

    ``seen_connected`` is the remembered fact that the pin has been LOW at some
    point, which upgrades the ambiguous HIGH reading to "connected, open".
    """
    printer = status.get("printer") or {}
    if "drawer_pin_high" not in printer:
        state = DRAWER_UNKNOWN
        pin_high = None
    else:
        pin_high = bool(printer["drawer_pin_high"])
        if not pin_high:
            state = DRAWER_CONNECTED_CLOSED
        elif seen_connected:
            state = DRAWER_CONNECTED_OPEN
        else:
            state = DRAWER_OPEN_OR_ABSENT

    label_de, label_en = DRAWER_TEXT[state]
    return {
        "state": state,
        "pin_high": pin_high,
        "connected": state in (DRAWER_CONNECTED_CLOSED, DRAWER_CONNECTED_OPEN),
        "certain": state in (DRAWER_CONNECTED_CLOSED, DRAWER_CONNECTED_OPEN),
        "label_de": label_de,
        "label_en": label_en,
        "explain_de": (
            "Der Drucker meldet nur den Pegel von Pin 3 der Kassenladen-Buchse. Eine "
            "geschlossene Lade zieht diesen Pin auf Masse - das ist eindeutig. Ein hoher "
            "Pegel bedeutet dagegen 'Lade offen' ODER 'keine Lade angeschlossen'; "
            "elektrisch sind beide Fälle identisch. Mit dem Test 'Kassenlade prüfen' "
            "lässt sich das aufklären."
        ),
        "explain_en": (
            "The printer only reports the level of pin 3 of the drawer connector. A closed "
            "drawer pulls that pin to ground, which is unambiguous. A high level means "
            "either 'drawer open' or 'no drawer connected' - electrically the two are "
            "identical. The 'Check cash drawer' test resolves it."
        ),
    }


def probe_drawer(transport: BaseTransport, pin: int = 0, settle: float = 1.2) -> Dict[str, Any]:
    """Active test: read the pin, fire the pulse, read again.

    A connected, closed drawer reads LOW, pops open on the pulse and then reads
    HIGH - a change that nothing else can produce.  If the pin is HIGH both
    before and after, either no drawer is attached or it was already open.
    """
    import time as _time

    result: Dict[str, Any] = {
        "before": None,
        "after": None,
        "changed": False,
        "verdict": DRAWER_UNKNOWN,
        "readable": bool(transport.bidirectional),
    }
    if not transport.bidirectional:
        return result

    before = read_status(transport)
    result["before"] = (before.get("printer") or {}).get("drawer_pin_high")

    try:
        transport.write(escpos.drawer_pulse(pin))
    except TransportError as exc:
        log.warning("Drawer probe failed: %s", exc)
        return result

    _time.sleep(settle)
    after = read_status(transport)
    result["after"] = (after.get("printer") or {}).get("drawer_pin_high")

    if result["before"] is None or result["after"] is None:
        result["verdict"] = DRAWER_UNKNOWN
    elif result["before"] != result["after"]:
        result["changed"] = True
        result["verdict"] = DRAWER_CONNECTED_OPEN
    elif result["before"] is False:
        result["verdict"] = DRAWER_CONNECTED_CLOSED
    else:
        result["verdict"] = DRAWER_OPEN_OR_ABSENT
    return result
