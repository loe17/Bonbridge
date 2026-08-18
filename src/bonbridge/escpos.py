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


def summarise_status(status: Dict[str, Dict[str, object]]) -> Tuple[str, List[str]]:
    """Reduce the four status groups to one traffic-light level and messages.

    Returns ``("ok" | "warn" | "error" | "unknown", [message, ...])``.
    """
    messages: List[str] = []
    level = "ok"

    if not status:
        return "unknown", ["Kein Status lesbar / no status readable"]

    printer = status.get("printer") or {}
    offline = status.get("offline") or {}
    error = status.get("error") or {}
    paper = status.get("paper") or {}

    if error.get("unrecoverable_error"):
        level = "error"
        messages.append("Unrecoverable printer error")
    if error.get("autocutter_error"):
        level = "error"
        messages.append("Auto cutter error - remove paper jam and restart")
    if error.get("recoverable_error") or error.get("auto_recoverable_error"):
        level = "error" if level == "error" else "warn"
        messages.append("Recoverable printer error")
    if offline.get("cover_open"):
        level = "error"
        messages.append("Cover open")
    if paper.get("paper_end"):
        level = "error"
        messages.append("Paper end")
    elif paper.get("paper_near_end"):
        level = "error" if level == "error" else "warn"
        messages.append("Paper near end")
    if printer.get("offline") and level == "ok":
        level = "warn"
        messages.append("Printer reports offline")

    if not messages:
        messages.append("OK")
    return level, messages


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
