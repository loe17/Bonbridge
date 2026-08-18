"""Kernel ``usblp`` transport (``/dev/usb/lp0``).

Fallback for hosts without libusb/pyusb and for printers that behave well as
plain USB printer class devices.  The device node is opened read/write so
status read-back still works - unlike the old ``socat -u`` setup, which was
write-only by construction.

References
----------
* Linux ``usblp`` driver and the IEEE 1284 device ID exposed in sysfs
  https://www.kernel.org/doc/html/latest/usb/index.html
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import glob
import logging
import os
import select
from typing import Any, Dict, List, Optional

from .base import BaseTransport, TransportError

log = logging.getLogger(__name__)

DEVICE_GLOB = "/dev/usb/lp*"


def available() -> bool:
    return bool(glob.glob(DEVICE_GLOB))


def enumerate_devices() -> List[Dict[str, Any]]:
    """List ``/dev/usb/lp*`` nodes together with their sysfs identity."""
    found: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(DEVICE_GLOB)):
        name = os.path.basename(path)
        info: Dict[str, Any] = {
            "transport": "usblp",
            "device": path,
            "label": path,
        }
        sysfs = f"/sys/class/usbmisc/{name}/device"
        ieee1284 = os.path.join(sysfs, "ieee1284_id")
        try:
            if os.path.exists(ieee1284):
                with open(ieee1284, "r", encoding="utf-8", errors="replace") as handle:
                    raw = handle.read().strip()
                info["ieee1284_id"] = raw
                for field in raw.split(";"):
                    if ":" not in field:
                        continue
                    key, _, value = field.partition(":")
                    key = key.strip().upper()
                    if key in ("MFG", "MANUFACTURER"):
                        info["manufacturer"] = value.strip()
                    elif key in ("MDL", "MODEL"):
                        info["product"] = value.strip()
                    elif key in ("SN", "SERN", "SERIALNUMBER"):
                        info["serial"] = value.strip()
                label = f"{info.get('manufacturer', '')} {info.get('product', '')}".strip()
                if label:
                    info["label"] = f"{label} ({path})"
        except OSError as exc:
            log.debug("Cannot read %s: %s", ieee1284, exc)
        found.append(info)
    return found


class UsbLpTransport(BaseTransport):
    """Read/write access to a ``/dev/usb/lpN`` character device."""

    type_name = "usblp"
    bidirectional = True

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        super().__init__(settings)
        self._fd: Optional[int] = None

    @property
    def device_path(self) -> str:
        configured = (self.settings.get("device") or "").strip()
        if configured:
            return configured
        candidates = sorted(glob.glob(DEVICE_GLOB))
        return candidates[0] if candidates else "/dev/usb/lp0"

    def open(self) -> None:
        with self._lock:
            if self._open:
                return
            path = self.device_path
            if not os.path.exists(path):
                raise TransportError(
                    f"{path} does not exist. Is the printer powered (24 V) and connected? "
                    "Check with: ls /dev/usb/ and dmesg | tail"
                )
            try:
                self._fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
            except OSError as write_exc:
                # Some kernels expose the node write-only; degrade gracefully.
                try:
                    self._fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
                    self.bidirectional = False
                    log.warning(
                        "%s could only be opened write-only (%s) - status read-back disabled",
                        path,
                        write_exc,
                    )
                except OSError as exc:
                    raise TransportError(f"Cannot open {path}: {exc}") from exc
            self._open = True
            log.info("usblp printer opened: %s", path)

    def close(self) -> None:
        with self._lock:
            self._open = False
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None

    def write(self, data: bytes) -> int:
        if not data:
            return 0
        with self._lock:
            if not self._open:
                self.open()
            assert self._fd is not None
            timeout = float(self.settings.get("write_timeout", 10.0))
            total = 0
            view = memoryview(data)
            while total < len(data):
                try:
                    _, writable, _ = select.select([], [self._fd], [], timeout)
                    if not writable:
                        raise TransportError(
                            f"Timeout writing to {self.device_path} - printer busy or offline"
                        )
                    total += os.write(self._fd, view[total:])
                except BlockingIOError:
                    continue
                except OSError as exc:
                    self.close()
                    raise TransportError(f"Write to {self.device_path} failed: {exc}") from exc
            return total

    def read(self, size: int = 64, timeout: float = 1.0) -> bytes:
        with self._lock:
            if not self._open or self._fd is None or not self.bidirectional:
                return b""
            try:
                readable, _, _ = select.select([self._fd], [], [], timeout)
                if not readable:
                    return b""
                return os.read(self._fd, size)
            except (BlockingIOError, InterruptedError):
                return b""
            except OSError as exc:
                log.debug("Read from %s failed: %s", self.device_path, exc)
                return b""

    def connection_label(self) -> str:
        return self.device_path
