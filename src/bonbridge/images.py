"""Turn an uploaded image into something a receipt printer can print.

A thermal printer has no idea what a JPEG is.  It prints dots: one bit per
dot, a fixed number of dots per line (512 on a TM-T88V, 576 on most 80 mm
clones, 384 on 58 mm ones).  Everything in this module exists to get from
"the user picked a photo" to exactly that, and - just as important - to show
the user the *same* bitmap on screen before it is committed to paper, because
a logo that looks fine in colour can turn into a black rectangle after
thresholding.

The preview returned here is not an approximation: it is the printed bitmap
itself, rendered back into a PNG.  What you see is what comes out.

Pillow does the decoding and the dithering.  It is an optional dependency
(``apt install python3-pil``); without it this module reports itself as
unavailable and the web interface says so instead of failing.

Command used
------------
``GS v 0`` - print raster bit image::

    GS  v  0  m  xL xH  yL yH  d1 ... dk

``m = 0`` is normal size, ``xL/xH`` is the row width in *bytes*, ``yL/yH`` the
number of rows.  Rows are sent in bands so that a long image does not have to
fit into the printer's buffer in one go.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger(__name__)

try:  # pragma: no cover - depends on the host
    from PIL import Image, ImageOps

    HAVE_PIL = True
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    HAVE_PIL = False

#: Dot width per paper size when the profile does not say.
DEFAULT_DOTS = {58: 384, 80: 576}

#: Rows per ``GS v 0`` command.  Small enough for any printer's buffer.
BAND_ROWS = 128

#: Refuse anything that would waste half a roll by accident.
MAX_ROWS = 4000

SUPPORTED = ("png", "jpg", "jpeg", "bmp", "gif", "webp", "tif", "tiff")


def availability() -> Dict[str, Any]:
    """Whether image printing can be offered, and what to do if not."""
    if HAVE_PIL:
        return {"available": True, "hint_de": "", "hint_en": "", "formats": list(SUPPORTED)}
    return {
        "available": False,
        "hint_de": (
            "Fuer den Bilddruck fehlt die Python-Bildbibliothek. "
            "Nachinstallieren mit:  sudo apt install python3-pil"
        ),
        "hint_en": (
            "Image printing needs the Python imaging library. "
            "Install it with:  sudo apt install python3-pil"
        ),
        "formats": [],
    }


def dots_for_profile(capabilities: Optional[Dict[str, Any]] = None) -> int:
    """Printable dots per line, taken from the profile where possible."""
    capabilities = capabilities or {}
    media = ((capabilities.get("profile") or {}).get("media") or {}) if capabilities else {}
    pixels = ((media.get("width") or {}) if isinstance(media, dict) else {}).get("pixels")
    try:
        value = int(pixels)
        if 100 <= value <= 2048:
            return value
    except (TypeError, ValueError):
        pass
    width_mm = capabilities.get("width_mm")
    try:
        return DEFAULT_DOTS[int(width_mm)]
    except (TypeError, ValueError, KeyError):
        return 576


def escpos_raster(packed: bytes, width_bytes: int, rows: int) -> bytes:
    """Wrap packed 1-bit rows into ``GS v 0`` commands, band by band."""
    out = bytearray()
    for start in range(0, rows, BAND_ROWS):
        band_rows = min(BAND_ROWS, rows - start)
        chunk = packed[start * width_bytes : (start + band_rows) * width_bytes]
        out += b"\x1d\x76\x30\x00"
        out += bytes((width_bytes & 0xFF, (width_bytes >> 8) & 0xFF))
        out += bytes((band_rows & 0xFF, (band_rows >> 8) & 0xFF))
        out += chunk
    return bytes(out)


def rasterise(
    data: bytes,
    *,
    dots: int = 576,
    scale_percent: int = 100,
    dither: bool = True,
    threshold: int = 128,
    invert: bool = False,
    align: str = "center",
) -> Dict[str, Any]:
    """Convert image bytes into ESC/POS raster data plus a true preview.

    Returns a dict with ``escpos`` (bytes), ``preview_png`` (base64 data URL),
    ``width``, ``height`` and ``notes``.
    """
    if not HAVE_PIL:
        raise RuntimeError(availability()["hint_en"])

    notes = []
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:  # noqa: BLE001 - user-supplied file
        raise ValueError(f"cannot read the image: {exc}") from exc

    source_format = (image.format or "?").lower()
    # Honour the orientation tag; phone photos are otherwise printed sideways.
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:  # noqa: BLE001
        pass

    if image.mode in ("RGBA", "LA", "P"):
        # Flatten transparency onto white - a thermal printer has no "no dot"
        # colour other than the paper itself.
        background = Image.new("RGB", image.size, (255, 255, 255))
        converted = image.convert("RGBA")
        background.paste(converted, mask=converted.split()[-1])
        image = background
        notes.append("transparency_flattened")

    image = image.convert("L")

    scale_percent = max(10, min(100, int(scale_percent or 100)))
    target_width = max(8, int(dots * scale_percent / 100))
    target_width -= target_width % 8  # whole bytes, no ragged right edge
    if image.width != target_width:
        height = max(1, round(image.height * target_width / image.width))
        resample = getattr(Image, "LANCZOS", None) or getattr(Image, "Resampling").LANCZOS
        image = image.resize((target_width, height), resample)

    if image.height > MAX_ROWS:
        image = image.crop((0, 0, image.width, MAX_ROWS))
        notes.append("truncated")

    if invert:
        image = ImageOps.invert(image)

    if dither:
        mono = image.convert("1")  # Floyd-Steinberg is Pillow's default here
    else:
        level = max(1, min(254, int(threshold)))
        mono = image.point(lambda value: 255 if value > level else 0, mode="1")

    # Place the (possibly narrower) image on a full-width canvas so the printer
    # does not need an alignment command for raster data - not every model
    # honours ESC a for GS v 0.
    width_bytes = (dots + 7) // 8
    canvas_width = width_bytes * 8
    if mono.width < canvas_width:
        canvas = Image.new("1", (canvas_width, mono.height), 1)  # 1 = white
        if align == "left":
            offset = 0
        elif align == "right":
            offset = canvas_width - mono.width
        else:
            offset = (canvas_width - mono.width) // 2
        canvas.paste(mono, (offset, 0))
        mono = canvas

    # Pillow's "1" mode has 0 = black; ESC/POS wants 1 = dot, so invert here.
    inverted = mono.point(lambda value: 0 if value else 1, mode="1")
    packed = inverted.tobytes()  # already 1 bit per pixel, MSB first, row padded

    escpos_bytes = escpos_raster(packed, width_bytes, mono.height)

    buffer = io.BytesIO()
    mono.convert("L").save(buffer, format="PNG", optimize=True)
    preview = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    return {
        "escpos": escpos_bytes,
        "preview_png": preview,
        "width": mono.width,
        "height": mono.height,
        "bytes": len(escpos_bytes),
        "format": source_format,
        "dither": bool(dither),
        "notes": notes,
    }


def looks_like_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def sniff(data: bytes) -> Tuple[str, str]:
    """(kind, detail) for an uploaded file, for a useful error message."""
    if looks_like_pdf(data):
        return "pdf", "PDF"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image", "PNG"
    if data[:3] == b"\xff\xd8\xff":
        return "image", "JPEG"
    if data[:2] == b"BM":
        return "image", "BMP"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image", "GIF"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image", "WebP"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "image", "TIFF"
    return "unknown", ""
