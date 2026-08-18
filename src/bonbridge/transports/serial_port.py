"""Serial transport (RS-232 / USB-serial / CDC-ACM).

Used for printers with an RS-232 interface board (Epson UB-S01), for
USB-to-serial bridges and for the ``/dev/ttyACM*`` devices that some Epson
models (for example the TM-M244A) expose instead of a printer class
interface.

Requires ``python3-serial`` (pyserial).

References
----------
* pySerial (BSD-3-Clause)  https://github.com/pyserial/pyserial
* Epson UB-S01 serial interface board settings: TM-T88V Technical Reference
  Guide  https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import glob
import logging
import os
from typing import Any, Dict, List, Optional

from .base import BaseTransport, TransportError

log = logging.getLogger(__name__)

try:  # pragma: no cover - depends on the host
    import serial

    HAVE_PYSERIAL = True
except ImportError:  # pragma: no cover
    serial = None  # type: ignore[assignment]
    HAVE_PYSERIAL = False

DEVICE_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS[0-9]", "/dev/serial/by-id/*")

#: Epson TM printers with a serial interface board default to 38400 8N1 with
#: DTR/DSR handshaking; the DIP switches on the UB-S01 board must match.
DEFAULT_BAUDRATE = 38400


def available() -> bool:
    return HAVE_PYSERIAL


def enumerate_devices() -> List[Dict[str, Any]]:
    if not HAVE_PYSERIAL:
        # Without pyserial these ports cannot be used, so do not offer them.
        return []
    found: List[Dict[str, Any]] = []
    seen = set()  # type: ignore[var-annotated]
    for pattern in DEVICE_GLOBS:
        for path in sorted(glob.glob(pattern)):
            real = os.path.realpath(path)
            if real in seen:
                continue
            seen.add(real)
            found.append(
                {
                    "transport": "serial",
                    "device": path,
                    "label": path,
                    "baudrate": DEFAULT_BAUDRATE,
                }
            )
    return found


class SerialTransport(BaseTransport):
    """Bidirectional serial line to a receipt printer."""

    type_name = "serial"
    bidirectional = True

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        super().__init__(settings)
        self._port: Any = None

    @property
    def device_path(self) -> str:
        return (self.settings.get("device") or "/dev/ttyUSB0").strip()

    def open(self) -> None:
        if not HAVE_PYSERIAL:
            raise TransportError("pyserial is not installed - install python3-serial")
        with self._lock:
            if self._open:
                return
            try:
                self._port = serial.Serial(
                    port=self.device_path,
                    baudrate=int(self.settings.get("baudrate") or DEFAULT_BAUDRATE),
                    bytesize=int(self.settings.get("bytesize") or 8),
                    parity=str(self.settings.get("parity") or "N")[0].upper(),
                    stopbits=float(self.settings.get("stopbits") or 1),
                    timeout=float(self.settings.get("read_timeout") or 1.0),
                    write_timeout=float(self.settings.get("write_timeout") or 10.0),
                    dsrdtr=bool(self.settings.get("dsrdtr", True)),
                    rtscts=bool(self.settings.get("rtscts", False)),
                    xonxoff=bool(self.settings.get("xonxoff", False)),
                )
            except Exception as exc:  # noqa: BLE001 - serial.SerialException et al.
                raise TransportError(f"Cannot open {self.device_path}: {exc}") from exc
            self._open = True
            log.info("Serial printer opened: %s @ %s baud", self.device_path, self._port.baudrate)

    def close(self) -> None:
        with self._lock:
            self._open = False
            if self._port is not None:
                try:
                    self._port.close()
                except Exception:  # noqa: BLE001
                    pass
                self._port = None

    def write(self, data: bytes) -> int:
        if not data:
            return 0
        with self._lock:
            if not self._open:
                self.open()
            try:
                written = self._port.write(data)
                self._port.flush()
                return int(written or 0)
            except Exception as exc:  # noqa: BLE001
                self.close()
                raise TransportError(f"Serial write failed: {exc}") from exc

    def read(self, size: int = 64, timeout: float = 1.0) -> bytes:
        with self._lock:
            if not self._open or self._port is None:
                return b""
            try:
                previous = self._port.timeout
                self._port.timeout = timeout
                try:
                    return self._port.read(size)
                finally:
                    self._port.timeout = previous
            except Exception as exc:  # noqa: BLE001
                log.debug("Serial read failed: %s", exc)
                return b""

    def connection_label(self) -> str:
        baud = self.settings.get("baudrate") or DEFAULT_BAUDRATE
        return f"{self.device_path} @ {baud}"
