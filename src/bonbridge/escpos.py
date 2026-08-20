"""ESC/POS command helpers, status decoding and built-in test pages.

Only the subset of ESC/POS that BonBridge itself needs is implemented here.
Print data coming from the POS application is passed through untouched - the
commands below are used for diagnostics, test prints and the optional
post-processing (cut / drawer pulse) configured per printer.

References:
  * Epson ESC/POS command reference (command set, status bit layouts)
    https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/index.html
  * TM-T88V supported commands
    https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmt88v.html
  * TM-T88V Technical Reference Guide (DIP switches, memory switches, boards)
    https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf
  * Code page numbers cross-checked against escpos-printer-db (CC BY 4.0)
    https://github.com/receipt-print-hq/escpos-printer-db
  * The test page layout deliberately mirrors the OrderAssist test receipt
    https://doku.order-assist.de/docs/handbuch/drucker/
  * Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md

ESC/POS is a trademark of Seiko Epson Corporation.  This module implements
only the publicly documented command set.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Raw command bytes
# --------------------------------------------------------------------------

ESC = b"\x1b"
GS = b"\x1d"
DLE = b"\x10"
EOT = b"\x04"
FS = b"\x1c"

INIT = ESC + b"@"  # ESC @   - initialise printer
LF = b"\n"

# Real-time status requests: DLE EOT n
DLE_EOT_PRINTER = DLE + EOT + b"\x01"
DLE_EOT_OFFLINE = DLE + EOT + b"\x02"
DLE_EOT_ERROR = DLE + EOT + b"\x03"
DLE_EOT_PAPER = DLE + EOT + b"\x04"

# GS r n - transmit status
GS_R_PAPER = GS + b"r\x01"
GS_R_DRAWER = GS + b"r\x02"

#: GS I n - transmit printer ID.  n=1 printer model, n=2 type, n=3 ROM version.
GS_I_MODEL = GS + b"I\x01"
GS_I_TYPE = GS + b"I\x02"
GS_I_ROM = GS + b"I\x03"

#: Code page numbers as used by ``ESC t n`` (subset, see escpos-printer-db).
CODEPAGES: Dict[str, int] = {
    "cp437": 0,
    "cp850": 2,
    "cp860": 3,
    "cp863": 4,
    "cp865": 5,
    "cp1252": 16,
    "cp866": 17,
    "cp852": 18,
    "cp858": 19,
    "cp775": 33,
    "cp1250": 45,
    "cp1251": 46,
    "cp1253": 47,
    "cp1254": 48,
    "cp1257": 51,
}

#: Python codec names for the code pages above.
CODEPAGE_CODECS: Dict[str, str] = {
    "cp437": "cp437",
    "cp850": "cp850",
    "cp860": "cp860",
    "cp863": "cp863",
    "cp865": "cp865",
    "cp1252": "cp1252",
    "cp866": "cp866",
    "cp852": "cp852",
    "cp858": "cp858",
    "cp775": "cp775",
    "cp1250": "cp1250",
    "cp1251": "cp1251",
    "cp1253": "cp1253",
    "cp1254": "cp1254",
    "cp1257": "cp1257",
}


def select_codepage(name: str) -> bytes:
    """``ESC t n`` - select the character code table."""
    number = CODEPAGES.get(name.lower())
    if number is None:
        return b""
    return ESC + b"t" + bytes([number])


def select_font(font: int) -> bytes:
    """``ESC M n`` - 0 = Font A, 1 = Font B."""
    return ESC + b"M" + bytes([1 if font else 0])


def align(mode: str) -> bytes:
    """``ESC a n`` - left / center / right."""
    return ESC + b"a" + bytes([{"left": 0, "center": 1, "right": 2}.get(mode, 0)])


def emphasis(on: bool) -> bytes:
    """``ESC E n`` - bold on/off."""
    return ESC + b"E" + bytes([1 if on else 0])


def double_size(on: bool) -> bytes:
    """``GS ! n`` - double width and height."""
    return GS + b"!" + bytes([0x11 if on else 0x00])


def feed(lines: int) -> bytes:
    """``ESC d n`` - feed n lines."""
    lines = max(0, min(255, int(lines)))
    return ESC + b"d" + bytes([lines]) if lines else b""


def cut(mode: str = "partial", feed_lines: int = 4) -> bytes:
    """``GS V m n`` - feed and cut.

    ``66`` (partial) / ``65`` (full) feed the paper by ``n`` dots before
    cutting, which every TM printer supports and which avoids cutting through
    the last printed line.
    """
    feed_dots = max(0, min(255, int(feed_lines) * 24))
    marker = 65 if mode == "full" else 66
    return GS + b"V" + bytes([marker, feed_dots])


def drawer_pulse(pin: int = 0, on_ms: int = 100, off_ms: int = 100) -> bytes:
    """``ESC p m t1 t2`` - fire the cash drawer kick-out solenoid."""
    m = 1 if pin else 0
    t1 = max(1, min(255, on_ms // 2))
    t2 = max(1, min(255, off_ms // 2))
    return ESC + b"p" + bytes([m, t1, t2])


def buzzer(times: int = 2, duration: int = 4) -> bytes:
    """``ESC ( A`` - buzzer, only available on some models."""
    times = max(1, min(63, int(times)))
    duration = max(1, min(255, int(duration)))
    return ESC + b"(A" + bytes([0x04, 0x00, 0x30, 0x37, times, duration])


def enable_asb(enabled: bool = True, mask: int = 0x0F) -> bytes:
    """``GS a n`` - Automatic Status Back."""
    return GS + b"a" + bytes([mask if enabled else 0])


def qrcode(data: str, size: int = 6, ecc: str = "M") -> bytes:
    """``GS ( k`` - store and print a QR code (model 2)."""
    payload = data.encode("utf-8", "replace")
    ecc_map = {"L": 48, "M": 49, "Q": 50, "H": 51}
    out = bytearray()
    # Select model 2
    out += GS + b"(k" + bytes([0x04, 0x00, 0x31, 0x41, 0x32, 0x00])
    # Module size
    out += GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x43, max(1, min(16, size))])
    # Error correction
    out += GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x45, ecc_map.get(ecc.upper(), 49)])
    # Store data
    length = len(payload) + 3
    out += GS + b"(k" + bytes([length & 0xFF, (length >> 8) & 0xFF, 0x31, 0x50, 0x30]) + payload
    # Print
    out += GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x51, 0x30])
    return bytes(out)


def barcode_code39(data: str, height: int = 60, width: int = 2) -> bytes:
    """``GS k 4`` - CODE39 barcode (NUL terminated form)."""
    payload = data.upper().encode("ascii", "replace")
    out = bytearray()
    out += GS + b"h" + bytes([max(1, min(255, height))])  # GS h - height
    out += GS + b"w" + bytes([max(2, min(6, width))])  # GS w - module width
    out += GS + b"H\x02"  # GS H - print HRI below barcode
    out += GS + b"k\x04" + payload + b"\x00"
    return bytes(out)


def encode_text(text: str, codepage: str = "cp1252") -> bytes:
    """Encode text for the printer, replacing unmappable characters."""
    codec = CODEPAGE_CODECS.get(codepage.lower(), "cp437")
    return text.encode(codec, "replace")


# --------------------------------------------------------------------------
# Status decoding
# --------------------------------------------------------------------------


def decode_printer_status(byte: int) -> Dict[str, object]:
    """Decode the answer to ``DLE EOT 1``."""
    return {
        "raw": byte,
        "drawer_pin_high": bool(byte & 0x04),
        "offline": bool(byte & 0x08),
    }


def decode_offline_status(byte: int) -> Dict[str, object]:
    """Decode the answer to ``DLE EOT 2``."""
    return {
        "raw": byte,
        "cover_open": bool(byte & 0x04),
        "paper_fed_by_button": bool(byte & 0x08),
        "paper_end_stop": bool(byte & 0x20),
        "error": bool(byte & 0x40),
    }


def decode_error_status(byte: int) -> Dict[str, object]:
    """Decode the answer to ``DLE EOT 3``."""
    return {
        "raw": byte,
        "recoverable_error": bool(byte & 0x04),
        "autocutter_error": bool(byte & 0x08),
        "unrecoverable_error": bool(byte & 0x20),
        "auto_recoverable_error": bool(byte & 0x40),
    }


def decode_paper_status(byte: int) -> Dict[str, object]:
    """Decode the answer to ``DLE EOT 4``."""
    near_end = bool(byte & 0x0C)
    end = bool(byte & 0x60)
    return {
        "raw": byte,
        "paper_near_end": near_end,
        "paper_end": end,
        "paper_ok": not (near_end or end),
    }


STATUS_DECODERS = {
    "printer": (DLE_EOT_PRINTER, decode_printer_status),
    "offline": (DLE_EOT_OFFLINE, decode_offline_status),
    "error": (DLE_EOT_ERROR, decode_error_status),
    "paper": (DLE_EOT_PAPER, decode_paper_status),
}


#: Status message keys and their German / English wording.  The daemon stores
#: keys, never prose, so the web interface can render them in either language
#: and the support report can print both.
STATUS_MESSAGES: Dict[str, Tuple[str, str]] = {
    "ok": ("Betriebsbereit", "Ready"),
    "no_status": (
        "Kein Status lesbar (Verbindung ohne Rueckkanal)",
        "No status readable (connection without a return channel)",
    ),
    "unrecoverable_error": (
        "Nicht behebbarer Druckerfehler - Drucker aus- und einschalten",
        "Unrecoverable printer error - power cycle the printer",
    ),
    "autocutter_error": (
        "Fehler am Papierschneider - Papierstau entfernen und neu starten",
        "Auto cutter error - clear the jam and restart",
    ),
    "recoverable_error": (
        "Behebbarer Druckerfehler",
        "Recoverable printer error",
    ),
    "cover_open": ("Deckel offen", "Cover open"),
    "paper_end": ("Papier leer", "Paper end"),
    "paper_near_end": ("Papier fast leer", "Paper near end"),
    "printer_offline": ("Drucker meldet offline", "Printer reports offline"),
    "not_connected": ("Nicht verbunden", "Not connected"),
    "drawer_closed": (
        "Kassenlade angeschlossen und geschlossen",
        "Cash drawer connected and closed",
    ),
    "drawer_open_or_absent": (
        "Kassenlade offen oder keine angeschlossen",
        "Cash drawer open or none connected",
    ),
}


def status_text(key: str, language: str = "de") -> str:
    """Human readable wording for a status key."""
    entry = STATUS_MESSAGES.get(key)
    if entry is None:
        return key
    return entry[0] if language.lower().startswith("de") else entry[1]


def status_texts(keys: List[str], language: str = "de") -> List[str]:
    return [status_text(key, language) for key in keys]


def summarise_status(status: Dict[str, Dict[str, object]]) -> Tuple[str, List[str]]:
    """Reduce the four status groups to a traffic-light level and message keys.

    Returns ``("ok" | "warn" | "error" | "unknown", [key, ...])`` where the
    keys index :data:`STATUS_MESSAGES`.
    """
    keys: List[str] = []
    level = "ok"

    if not status:
        return "unknown", ["no_status"]

    printer = status.get("printer") or {}
    offline = status.get("offline") or {}
    error = status.get("error") or {}
    paper = status.get("paper") or {}

    if error.get("unrecoverable_error"):
        level = "error"
        keys.append("unrecoverable_error")
    if error.get("autocutter_error"):
        level = "error"
        keys.append("autocutter_error")
    if error.get("recoverable_error") or error.get("auto_recoverable_error"):
        level = "error" if level == "error" else "warn"
        keys.append("recoverable_error")
    if offline.get("cover_open"):
        level = "error"
        keys.append("cover_open")
    if paper.get("paper_end"):
        level = "error"
        keys.append("paper_end")
    elif paper.get("paper_near_end"):
        level = "error" if level == "error" else "warn"
        keys.append("paper_near_end")
    if printer.get("offline") and level == "ok":
        level = "warn"
        keys.append("printer_offline")

    if not keys:
        keys.append("ok")
    return level, keys


# --------------------------------------------------------------------------
# Test pages
# --------------------------------------------------------------------------


def _rule(width: int) -> str:
    return "-" * width


def test_page(
    *,
    title: str = "BonBridge Testseite",
    printer_name: str = "",
    connection: str = "",
    model: str = "",
    columns: int = 42,
    font: int = 0,
    codepage: str = "cp1252",
    extra_lines: Optional[List[str]] = None,
    qr_payload: str = "",
    do_cut: bool = True,
) -> bytes:
    """Build the BonBridge test receipt.

    Deliberately modelled on the OrderAssist test page so the values printed
    here can be typed straight into the app: character-per-line ruler,
    special characters, alignment, table, divider and a QR code.
    """
    out = bytearray()
    out += INIT
    out += select_codepage(codepage)
    out += select_font(font)

    def line(text: str = "") -> None:
        out.extend(encode_text(text, codepage) + LF)

    out += align("center")
    out += emphasis(True)
    line(title)
    out += emphasis(False)
    out += align("left")
    line()

    if printer_name:
        line(f"Drucker:      {printer_name}")
    if connection:
        line(f"Verbindung:   {connection}")
    if model:
        line(f"Druckertyp:   {model}")
    line(f"Schriftart:   font{font + 1}")
    line(f"Zeichensatz:  {codepage}")
    line(f"Zeilenbreite: {columns}")
    for entry in extra_lines or []:
        line(entry)
    line()

    line("Anzahl Zeichen pro Zeile:")
    for width in range(32, 76, 4):
        line(f"{width}:{_rule(width - len(str(width)) - 1)}")
    line()

    line("Sonderzeichen:")
    for char, name in (
        ("€", "Euro"),
        ("ß", "scharfes S"),
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("ÄÖÜ", "AE OE UE"),
    ):
        line(f">{char}< ({name})")
    line()

    line("Textausrichtung:")
    out += align("left")
    line("Links")
    out += align("center")
    line("Mittig")
    out += align("right")
    line("Rechts")
    out += align("left")
    line()

    line("Tabelle:")
    line("A      B      C      D")
    line("€      ß      ä      ö")
    line()

    line("Divider:")
    line(_rule(columns))
    line("=" * columns)
    line()

    if qr_payload:
        line("QR-Code:")
        out += align("center")
        out += qrcode(qr_payload, size=6)
        out += LF
        out += align("left")
        line()

    line(_rule(columns))
    if do_cut:
        out += cut("partial", feed_lines=4)
    else:
        out += feed(5)
    return bytes(out)


def feature_test_page(
    *,
    columns: int = 42,
    codepage: str = "cp1252",
    with_barcode: bool = True,
    with_qr: bool = True,
    do_cut: bool = True,
) -> bytes:
    """Short page exercising barcode / QR / emphasis / double size."""
    out = bytearray()
    out += INIT + select_codepage(codepage)

    def line(text: str = "") -> None:
        out.extend(encode_text(text, codepage) + LF)

    out += align("center") + emphasis(True)
    line("BonBridge Funktionstest")
    out += emphasis(False) + align("left")
    line("-" * columns)
    out += double_size(True)
    line("Doppelt")
    out += double_size(False)
    out += emphasis(True)
    line("Fett")
    out += emphasis(False)
    line("Normal")
    line("-" * columns)
    if with_barcode:
        line("CODE39:")
        out += align("center") + barcode_code39("BONBRIDGE") + align("left")
        line()
    if with_qr:
        line("QR:")
        out += align("center") + qrcode("BonBridge", size=5) + LF + align("left")
        line()
    line("-" * columns)
    if do_cut:
        out += cut("partial", feed_lines=4)
    else:
        out += feed(5)
    return bytes(out)


def wrap_line(text: str, columns: int) -> List[str]:
    """Word-wrap one logical line to the printer's column count.

    A line that already fits is returned untouched - re-joining it on single
    spaces would destroy deliberate padding (a right-aligned amount produced by
    :func:`pad_columns`) and any indentation the user typed.
    """
    if columns <= 0 or len(text) <= columns:
        return [text]
    words = text.split(" ")
    lines: List[str] = []
    current = ""
    for word in words:
        while len(word) > columns:  # a single word longer than the paper
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:columns])
            word = word[columns:]
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) > columns:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return lines or [""]


def pad_columns(left: str, right: str, columns: int) -> str:
    """``left`` flush left, ``right`` flush right, one line, never overflowing."""
    right = right[:columns]
    space = columns - len(right)
    if space <= 1:
        return right.rjust(columns)
    return f"{left[: space - 1]:<{space - 1}} {right}"


def status_report_page(
    *,
    title: str,
    lines: List[Tuple[str, str]],
    hints: List[str],
    columns: int = 42,
    font: int = 0,
    codepage: str = "cp1252",
    qr_payload: str = "",
    do_cut: bool = True,
    big_value: str = "",
    big_label: str = "",
) -> bytes:
    """The slip printed on start-up: what the POS application needs to know.

    The IP address is printed twice - once in double size so it can be read
    from across the counter, once in the key/value block.
    """
    out = bytearray()
    out += INIT + select_codepage(codepage) + select_font(font)

    def line(text: str = "") -> None:
        out.extend(encode_text(text, codepage) + LF)

    out += align("center") + emphasis(True)
    line(title)
    out += emphasis(False)
    line("=" * columns)

    if big_value:
        line()
        if big_label:
            line(big_label)
        out += double_size(True) + emphasis(True)
        line(big_value)
        out += double_size(False) + emphasis(False)
        line()

    out += align("left")
    for key, value in lines:
        line(pad_columns(key, value, columns))

    if hints:
        line("-" * columns)
        for hint in hints:
            for wrapped in wrap_line(hint, columns):
                line(wrapped)

    if qr_payload:
        line()
        out += align("center")
        out += qrcode(qr_payload, size=6)
        out += LF
        for wrapped in wrap_line(qr_payload, columns):
            line(wrapped)
        out += align("left")

    line("=" * columns)
    if do_cut:
        out += cut("partial", feed_lines=4)
    else:
        out += feed(5)
    return bytes(out)


def network_alert_page(
    *,
    online: bool,
    printer_name: str,
    reason: str = "",
    columns: int = 42,
    codepage: str = "cp1252",
    language: str = "de",
    timestamp: str = "",
    rows: Optional[List[Tuple[str, str]]] = None,
    outage: str = "",
    address: str = "",
    do_cut: bool = True,
) -> bytes:
    """Slip printed when the device loses or regains its network connection.

    The printer is reachable over USB even while the network is down, so it is
    the one component that can still tell somebody what actually happened -
    which beats "the printer is broken" as a diagnosis.
    """
    german = language.lower().startswith("de")
    if online:
        heading = "NETZWERK WIEDER DA" if german else "NETWORK IS BACK"
        body = (
            [
                "Die Netzwerkverbindung steht wieder.",
                "Das Kassensystem kann wieder drucken.",
            ]
            if german
            else [
                "The network connection is back.",
                "The POS application can print again.",
            ]
        )
    else:
        heading = "KEINE NETZWERKVERBINDUNG" if german else "NO NETWORK CONNECTION"
        body = (
            [
                "Dieses Geraet ist gerade nicht im Netzwerk.",
                "Das Kassensystem kann diesen Drucker",
                "deshalb nicht erreichen - der Drucker",
                "selbst ist in Ordnung.",
                "",
                "Bitte pruefen:",
                "- LAN-Kabel an Geraet und Switch",
                "- Switch/Router eingeschaltet",
                "- bei WLAN: Reichweite und Passwort",
            ]
            if german
            else [
                "This device is currently off the network.",
                "The POS application cannot reach this",
                "printer - the printer itself is fine.",
                "",
                "Please check:",
                "- LAN cable at the device and the switch",
                "- switch/router powered on",
                "- for Wi-Fi: range and password",
            ]
        )

    out = bytearray()
    out += INIT + select_codepage(codepage)

    def line(text: str = "") -> None:
        out.extend(encode_text(text, codepage) + LF)

    out += align("center")
    line("*" * columns)
    out += emphasis(True)
    if len(heading) <= max(1, columns // 2):
        out += double_size(True)
        line(heading)
        out += double_size(False)
    else:
        line(heading)
    out += emphasis(False)
    line("*" * columns)
    out += align("left")
    line()
    line(("Drucker: " if german else "Printer: ") + printer_name)
    if timestamp:
        line(("Zeit:    " if german else "Time:    ") + timestamp)
    if outage:
        line(("Ausfall: " if german else "Outage:  ") + outage)
    if address:
        line(("Adresse: " if german else "Address: ") + address)
    if reason:
        line()
        for wrapped in wrap_line(reason, columns):
            line(wrapped)
    if rows:
        line("-" * columns)
        for key, value in rows:
            line(pad_columns(key, value, columns))
    line("-" * columns)
    for text in body:
        if not text:
            line()
            continue
        for wrapped in wrap_line(text, columns):
            line(wrapped)
    line()
    line("=" * columns)
    if do_cut:
        out += cut("partial", feed_lines=4)
    else:
        out += feed(5)
    return bytes(out)


def paper_low_page(
    *,
    printer_name: str,
    columns: int = 42,
    codepage: str = "cp1252",
    language: str = "de",
    timestamp: str = "",
    do_cut: bool = True,
) -> bytes:
    """Short warning slip printed once when the paper roll runs low."""
    german = language.lower().startswith("de")
    heading = "PAPIER FAST LEER" if german else "PAPER LOW"
    body = (
        [
            "Die Papierrolle geht zur Neige.",
            "Bitte bei naechster Gelegenheit wechseln,",
            "damit keine Bons verloren gehen.",
        ]
        if german
        else [
            "The paper roll is running out.",
            "Please replace it at the next opportunity",
            "so that no receipts are lost.",
        ]
    )
    out = bytearray()
    out += INIT + select_codepage(codepage)

    def line(text: str = "") -> None:
        out.extend(encode_text(text, codepage) + LF)

    out += align("center")
    line("*" * columns)
    out += double_size(True) + emphasis(True)
    line(heading)
    out += double_size(False) + emphasis(False)
    line("*" * columns)
    out += align("left")
    line()
    line(("Drucker: " if german else "Printer: ") + printer_name)
    if timestamp:
        line(("Zeit:    " if german else "Time:    ") + timestamp)
    line()
    for text in body:
        for wrapped in wrap_line(text, columns):
            line(wrapped)
    line()
    line("-" * columns)
    if do_cut:
        out += cut("partial", feed_lines=4)
    else:
        out += feed(5)
    return bytes(out)
