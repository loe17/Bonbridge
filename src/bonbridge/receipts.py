"""Compose a receipt from a simple description, for printing *and* preview.

The web interface lets you type a receipt and see how it will look on paper
before anything is printed.  Preview and print must never drift apart, so both
come out of the same function here: :func:`compose` returns the ESC/POS byte
stream **and** a line-by-line preview carrying the same alignment, emphasis and
size attributes.

Element types accepted in ``spec["elements"]``:

===============  =========================================================
``text``         ``text``, optional ``align``, ``bold``, ``size``
``kv``           ``left`` / ``right`` - description flush left, amount right
``divider``      optional ``char`` (default ``-``)
``blank``        empty line, optional ``count``
``barcode``      ``data`` (CODE39)
``qr``           ``data``
===============  =========================================================

``size`` is ``normal`` or ``double``.  ``align`` is ``left``, ``center`` or
``right``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import escpos

MAX_ELEMENTS = 200
MAX_TEXT = 4000


def _clean_align(value: Any) -> str:
    value = str(value or "left").lower()
    return value if value in ("left", "center", "right") else "left"


def _preview_line(
    text: str, align: str = "left", bold: bool = False, double: bool = False, kind: str = "text"
) -> Dict[str, Any]:
    return {"text": text, "align": align, "bold": bool(bold), "double": bool(double), "kind": kind}


def compose(
    spec: Dict[str, Any],
    *,
    columns: int = 42,
    codepage: str = "cp1252",
    font: int = 0,
    can_cut: bool = True,
    can_drawer: bool = True,
    can_barcode: bool = True,
    can_qr: bool = True,
) -> Tuple[bytes, List[Dict[str, Any]], List[str]]:
    """Build a receipt.

    Returns ``(escpos_bytes, preview_lines, notes)``.  ``notes`` lists what was
    skipped because the printer cannot do it, so the interface can say why.
    """
    notes: List[str] = []
    preview: List[Dict[str, Any]] = []
    out = bytearray()
    out += escpos.INIT + escpos.select_codepage(codepage) + escpos.select_font(font)

    current_align = "left"

    def set_align(align: str) -> None:
        nonlocal current_align
        if align != current_align:
            out.extend(escpos.align(align))
            current_align = align

    def emit(
        text: str, align: str, bold: bool, double: bool, kind: str = "text", wrap: bool = True
    ) -> None:
        width = max(1, columns // 2) if double else columns
        chunks = escpos.wrap_line(text, width) if wrap else [text]
        for chunk in chunks:
            set_align(align)
            if bold:
                out.extend(escpos.emphasis(True))
            if double:
                out.extend(escpos.double_size(True))
            out.extend(escpos.encode_text(chunk, codepage) + escpos.LF)
            if double:
                out.extend(escpos.double_size(False))
            if bold:
                out.extend(escpos.emphasis(False))
            preview.append(_preview_line(chunk, align, bold, double, kind))

    elements = spec.get("elements") or []
    if not isinstance(elements, list):
        elements = []
    elements = elements[:MAX_ELEMENTS]

    for element in elements:
        if not isinstance(element, dict):
            continue
        kind = str(element.get("type") or "text").lower()

        if kind == "blank":
            count = max(1, min(10, int(element.get("count") or 1)))
            for _ in range(count):
                out.extend(escpos.LF)
                preview.append(_preview_line("", "left", False, False, "blank"))

        elif kind == "divider":
            char = (str(element.get("char") or "-") or "-")[0]
            emit(char * columns, "left", False, False, "divider", wrap=False)

        elif kind == "kv":
            left = str(element.get("left") or "")[:MAX_TEXT]
            right = str(element.get("right") or "")[:MAX_TEXT]
            bold = bool(element.get("bold"))
            # Already padded to exactly `columns`; wrapping would collapse the
            # padding and the amount would no longer be flush right.
            emit(escpos.pad_columns(left, right, columns), "left", bold, False, "kv", wrap=False)

        elif kind == "barcode":
            data = str(element.get("data") or "").strip()[:64]
            if not data:
                continue
            if not can_barcode:
                notes.append("barcode_unsupported")
                continue
            set_align("center")
            out.extend(escpos.barcode_code39(data))
            out.extend(escpos.LF)
            preview.append(_preview_line(data, "center", False, False, "barcode"))

        elif kind == "qr":
            data = str(element.get("data") or "").strip()[:512]
            if not data:
                continue
            if not can_qr:
                notes.append("qr_unsupported")
                continue
            set_align("center")
            out.extend(escpos.qrcode(data, size=int(element.get("size") or 6)))
            out.extend(escpos.LF)
            preview.append(_preview_line(data, "center", False, False, "qr"))

        else:  # text
            text = str(element.get("text") or "")[:MAX_TEXT]
            align = _clean_align(element.get("align"))
            bold = bool(element.get("bold"))
            double = str(element.get("size") or "normal").lower() == "double"
            if text == "":
                out.extend(escpos.LF)
                preview.append(_preview_line("", align, False, False, "blank"))
            else:
                emit(text, align, bold, double)

    set_align("left")

    feed_lines = max(0, min(10, int(spec.get("feed") or 0)))
    if feed_lines:
        out.extend(escpos.feed(feed_lines))
        for _ in range(feed_lines):
            preview.append(_preview_line("", "left", False, False, "blank"))

    if spec.get("cut", True):
        if can_cut:
            out.extend(escpos.cut("partial", feed_lines=4))
            # The label is rendered by the interface so it follows its language.
            preview.append(_preview_line("", "center", False, False, "cut"))
        else:
            notes.append("cutter_unsupported")
            out.extend(escpos.feed(5))

    if spec.get("open_drawer"):
        if can_drawer:
            out.extend(escpos.drawer_pulse(0))
            preview.append(_preview_line("", "center", False, False, "drawer"))
        else:
            notes.append("drawer_unsupported")

    return bytes(out), preview, notes


def spec_from_text(
    text: str,
    *,
    title: str = "",
    footer: str = "",
    cut: bool = True,
    open_drawer: bool = False,
    qr: str = "",
) -> Dict[str, Any]:
    """Turn a plain multi-line text into a receipt spec.

    Convenience for the simple case: a title, some lines, a footer.  A line
    consisting only of ``---`` becomes a divider; ``key | value`` becomes a
    left/right pair, which is what price lines usually want.
    """
    elements: List[Dict[str, Any]] = []
    if title:
        elements.append({"type": "text", "text": title, "align": "center", "bold": True, "size": "double"})
        elements.append({"type": "divider"})

    for raw in (text or "").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped in ("---", "***", "==="):
            elements.append({"type": "divider", "char": "=" if stripped == "===" else "-"})
        elif "|" in line:
            left, _, right = line.partition("|")
            elements.append({"type": "kv", "left": left.strip(), "right": right.strip()})
        else:
            elements.append({"type": "text", "text": line})

    if footer:
        elements.append({"type": "divider"})
        elements.append({"type": "text", "text": footer, "align": "center"})
    if qr:
        elements.append({"type": "qr", "data": qr})

    return {"elements": elements, "cut": cut, "open_drawer": open_drawer, "feed": 1}
