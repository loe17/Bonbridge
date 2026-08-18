"""USB transport based on libusb (pyusb).

This is the default and the reason BonBridge works with printers the old
``socat`` setup could not handle:  models such as the Epson TM-m30 family or
the TM-M244A do **not** present themselves as USB printer class devices, so
``/dev/usb/lp0`` never appears.  Talking to the bulk endpoints directly via
libusb works for both classes of device and additionally gives us the IN
endpoint, i.e. real status read-back.

Requires ``python3-usb`` (pyusb) and libusb.  If pyusb is missing the
transport reports itself as unavailable and the daemon falls back to
``usblp``.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from .base import BaseTransport, TransportError

log = logging.getLogger(__name__)

try:  # pragma: no cover - depends on the host
    import usb.core
    import usb.util

    HAVE_PYUSB = True
except Exception:  # noqa: BLE001 - pyusb raises various errors when libusb is absent
    usb = None  # type: ignore[assignment]
    HAVE_PYUSB = False


#: USB device class 7 = printer.
USB_CLASS_PRINTER = 0x07

#: Vendors known to build ESC/POS receipt printers.  Used to also offer
#: vendor-specific devices (class 0xFF) during auto-detection.
KNOWN_VENDORS: Dict[int, str] = {
    0x04B8: "Seiko Epson",
    0x0519: "Star Micronics",
    0x0DD4: "Custom / Bixolon",
    0x1504: "Bixolon",
    0x0416: "Winbond (generic POS)",
    0x0483: "STMicroelectronics (generic POS)",
    0x6868: "Zjiang / generic",
    0x0FE6: "ICS Advent / generic",
    0x1FC9: "NXP (generic POS)",
    0x28E9: "GigaDevice (generic POS)",
    0x20D1: "Rongta",
    0x1CBE: "Texas Instruments (generic POS)",
    0x154F: "SNBC",
    0x0525: "Netchip / generic",
    0x1A86: "QinHeng CH34x bridge",
    0x067B: "Prolific bridge",
}


def available() -> bool:
    return HAVE_PYUSB


def _string_safe(device: Any, index: Optional[int]) -> str:
    if not index:
        return ""
    try:
        return usb.util.get_string(device, index) or ""
    except Exception:  # noqa: BLE001 - descriptor reads often need root
        return ""


def enumerate_devices() -> List[Dict[str, Any]]:
    """List USB devices that look like receipt printers."""
    if not HAVE_PYUSB:
        return []
    found: List[Dict[str, Any]] = []
    try:
        devices = list(usb.core.find(find_all=True))
    except Exception as exc:  # noqa: BLE001
        log.warning("USB enumeration failed: %s", exc)
        return []

    for device in devices:
        try:
            interfaces = []
            is_printer_class = False
            for configuration in device:
                for interface in configuration:
                    interfaces.append(
                        {
                            "number": interface.bInterfaceNumber,
                            "class": interface.bInterfaceClass,
                            "subclass": interface.bInterfaceSubClass,
                            "protocol": interface.bInterfaceProtocol,
                        }
                    )
                    if interface.bInterfaceClass == USB_CLASS_PRINTER:
                        is_printer_class = True
            vendor_known = device.idVendor in KNOWN_VENDORS
            if not (is_printer_class or vendor_known):
                continue
            found.append(
                {
                    "transport": "usb",
                    "vendor_id": device.idVendor,
                    "product_id": device.idProduct,
                    "vendor_id_hex": f"{device.idVendor:04x}",
                    "product_id_hex": f"{device.idProduct:04x}",
                    "manufacturer": _string_safe(device, device.iManufacturer)
                    or KNOWN_VENDORS.get(device.idVendor, ""),
                    "product": _string_safe(device, device.iProduct),
                    "serial": _string_safe(device, device.iSerialNumber),
                    "bus": getattr(device, "bus", None),
                    "address": getattr(device, "address", None),
                    "printer_class": is_printer_class,
                    "interfaces": interfaces,
                    "label": (
                        f"{_string_safe(device, device.iManufacturer) or KNOWN_VENDORS.get(device.idVendor, 'USB')} "
                        f"{_string_safe(device, device.iProduct) or ''}".strip()
                        + f" ({device.idVendor:04x}:{device.idProduct:04x})"
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001 - a broken device must not stop the scan
            log.debug("Skipping USB device during enumeration: %s", exc)
    return found


class UsbTransport(BaseTransport):
    """Talk to a USB printer through libusb bulk endpoints."""

    type_name = "usb"
    bidirectional = True

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        super().__init__(settings)
        self._device: Any = None
        self._out_ep: Any = None
        self._in_ep: Any = None
        self._interface_number: Optional[int] = None
        self._detached = False

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip().lower()
        try:
            return int(text, 16) if text.startswith("0x") else int(text, 0)
        except ValueError:
            return None

    def _find_device(self) -> Any:
        vendor_id = self._as_int(self.settings.get("vendor_id"))
        product_id = self._as_int(self.settings.get("product_id"))
        serial = (self.settings.get("serial") or "").strip()

        criteria: Dict[str, Any] = {}
        if vendor_id is not None:
            criteria["idVendor"] = vendor_id
        if product_id is not None:
            criteria["idProduct"] = product_id

        candidates = list(usb.core.find(find_all=True, **criteria))
        if serial:
            filtered = []
            for candidate in candidates:
                if _string_safe(candidate, candidate.iSerialNumber) == serial:
                    filtered.append(candidate)
            candidates = filtered or candidates

        if not candidates:
            raise TransportError(
                "USB printer not found "
                f"(vendor_id={vendor_id}, product_id={product_id}, serial={serial or '-'})"
            )
        return candidates[0]

    def _select_endpoints(self, device: Any) -> None:
        configuration = None
        try:
            configuration = device.get_active_configuration()
        except Exception:  # noqa: BLE001 - device not configured yet
            device.set_configuration()
            configuration = device.get_active_configuration()

        preferred = None
        fallback = None
        for interface in configuration:
            out_ep = usb.util.find_descriptor(
                interface,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                == usb.util.ENDPOINT_OUT
                and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK,
            )
            if out_ep is None:
                continue
            in_ep = usb.util.find_descriptor(
                interface,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                == usb.util.ENDPOINT_IN
                and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK,
            )
            entry = (interface, out_ep, in_ep)
            if interface.bInterfaceClass == USB_CLASS_PRINTER:
                preferred = entry
                break
            if fallback is None:
                fallback = entry

        chosen = preferred or fallback
        if chosen is None:
            raise TransportError("No bulk OUT endpoint found on this USB device")

        interface, out_ep, in_ep = chosen
        self._interface_number = interface.bInterfaceNumber
        self._out_ep = out_ep
        self._in_ep = in_ep

    # -- lifecycle ---------------------------------------------------------

    def open(self) -> None:
        if not HAVE_PYUSB:
            raise TransportError(
                "pyusb is not installed - install python3-usb or use the 'usblp' transport"
            )
        with self._lock:
            if self._open:
                return
            device = self._find_device()

            # Hand the device over from the kernel's usblp driver to us.
            try:
                for configuration in device:
                    for interface in configuration:
                        number = interface.bInterfaceNumber
                        try:
                            if device.is_kernel_driver_active(number):
                                device.detach_kernel_driver(number)
                                self._detached = True
                        except (NotImplementedError, AttributeError):
                            pass
                        except Exception as exc:  # noqa: BLE001
                            log.debug("Could not detach kernel driver on if %s: %s", number, exc)
            except Exception as exc:  # noqa: BLE001
                log.debug("Kernel driver handling failed: %s", exc)

            self._select_endpoints(device)
            try:
                usb.util.claim_interface(device, self._interface_number)
            except Exception as exc:  # noqa: BLE001 - some kernels claim implicitly
                log.debug("claim_interface failed (continuing): %s", exc)

            self._device = device
            self._open = True
            log.info(
                "USB printer opened: %04x:%04x interface %s (in-endpoint: %s)",
                device.idVendor,
                device.idProduct,
                self._interface_number,
                "yes" if self._in_ep is not None else "no",
            )

    def close(self) -> None:
        with self._lock:
            device = self._device
            self._open = False
            self._device = None
            self._out_ep = None
            self._in_ep = None
            if device is None:
                return
            try:
                if self._interface_number is not None:
                    usb.util.release_interface(device, self._interface_number)
            except Exception:  # noqa: BLE001
                pass
            try:
                usb.util.dispose_resources(device)
            except Exception:  # noqa: BLE001
                pass
            if self._detached:
                try:
                    device.attach_kernel_driver(self._interface_number)
                except Exception:  # noqa: BLE001
                    pass
                self._detached = False

    # -- I/O ---------------------------------------------------------------

    def write(self, data: bytes) -> int:
        if not data:
            return 0
        with self._lock:
            if not self._open:
                self.open()
            assert self._out_ep is not None
            chunk_size = int(self.settings.get("chunk_size") or 4096)
            timeout_ms = int(float(self.settings.get("write_timeout", 10.0)) * 1000)
            written = 0
            try:
                for offset in range(0, len(data), chunk_size):
                    chunk = data[offset : offset + chunk_size]
                    written += self._out_ep.write(chunk, timeout_ms)
            except Exception as exc:  # noqa: BLE001 - usb.core.USBError and friends
                self.close()
                raise TransportError(f"USB write failed: {exc}") from exc
            return written

    def read(self, size: int = 64, timeout: float = 1.0) -> bytes:
        with self._lock:
            if not self._open or self._in_ep is None:
                return b""
            try:
                data = self._in_ep.read(size, int(timeout * 1000))
                return bytes(bytearray(data))
            except Exception as exc:  # noqa: BLE001 - a timeout is normal here
                message = str(exc).lower()
                if "timeout" in message or "timed out" in message:
                    return b""
                log.debug("USB read failed: %s", exc)
                return b""

    # -- description -------------------------------------------------------

    def connection_label(self) -> str:
        vendor = self._as_int(self.settings.get("vendor_id"))
        product = self._as_int(self.settings.get("product_id"))
        if vendor is not None and product is not None:
            return f"USB {vendor:04x}:{product:04x}"
        return "USB (auto)"

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info["in_endpoint"] = self._in_ep is not None
        info["interface"] = self._interface_number
        info["pyusb"] = HAVE_PYUSB
        return info


def wait_for_device(vendor_id: int, product_id: int, timeout: float = 10.0) -> bool:
    """Block until the given USB device shows up (used after a power cycle)."""
    if not HAVE_PYUSB:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if usb.core.find(idVendor=vendor_id, idProduct=product_id) is not None:
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
    return False
