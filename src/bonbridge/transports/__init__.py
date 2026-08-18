"""Transport factory and device discovery."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseTransport, TransportError
from . import network, serial_port, usb_libusb, usblp

log = logging.getLogger(__name__)

TRANSPORTS = {
    "usb": usb_libusb.UsbTransport,
    "usblp": usblp.UsbLpTransport,
    "serial": serial_port.SerialTransport,
    "network": network.NetworkTransport,
}

__all__ = [
    "BaseTransport",
    "TransportError",
    "TRANSPORTS",
    "build_transport",
    "scan_devices",
    "autodetect_settings",
    "runtime_report",
]


def build_transport(settings: Optional[Dict[str, Any]]) -> BaseTransport:
    """Create a transport instance from a configuration fragment.

    ``{"type": "auto"}`` picks the best available local device: a libusb
    capable USB printer first, then ``/dev/usb/lp*``, then a serial port.
    """
    settings = dict(settings or {})
    kind = str(settings.pop("type", "auto") or "auto").lower()

    if kind == "auto":
        detected = autodetect_settings()
        if detected is None:
            raise TransportError(
                "No local printer found. Connect the printer, make sure it has its own "
                "24 V power supply, then rescan in the web interface."
            )
        kind = detected.pop("type")
        merged = dict(detected)
        merged.update(settings)
        settings = merged

    factory = TRANSPORTS.get(kind)
    if factory is None:
        raise TransportError(f"Unknown transport type: {kind}")
    return factory(settings)


def scan_devices() -> List[Dict[str, Any]]:
    """Enumerate everything that could be a printer, for the web interface."""
    devices: List[Dict[str, Any]] = []
    for module in (usb_libusb, usblp, serial_port):
        try:
            devices.extend(module.enumerate_devices())
        except Exception as exc:  # noqa: BLE001 - a failing scanner must not break the page
            log.warning("Device scan via %s failed: %s", module.__name__, exc)
    return devices


def autodetect_settings() -> Optional[Dict[str, Any]]:
    """Return transport settings for the most plausible local printer."""
    usb_devices = []
    try:
        usb_devices = usb_libusb.enumerate_devices()
    except Exception as exc:  # noqa: BLE001
        log.debug("USB autodetect failed: %s", exc)

    # Prefer real USB printer class devices, then known vendors.
    for entry in sorted(usb_devices, key=lambda e: (not e.get("printer_class"),)):
        return {
            "type": "usb",
            "vendor_id": entry["vendor_id"],
            "product_id": entry["product_id"],
            "serial": entry.get("serial") or None,
        }

    lp_devices = usblp.enumerate_devices()
    if lp_devices:
        return {"type": "usblp", "device": lp_devices[0]["device"]}

    serial_devices = serial_port.enumerate_devices()
    if serial_devices:
        return {
            "type": "serial",
            "device": serial_devices[0]["device"],
            "baudrate": serial_port.DEFAULT_BAUDRATE,
        }
    return None


def runtime_report() -> Dict[str, Any]:
    """Which transports can actually be used on this machine."""
    return {
        "usb": {
            "available": usb_libusb.available(),
            "hint": "python3-usb (pyusb) + libusb",
        },
        "usblp": {
            "available": usblp.available(),
            "hint": "kernel module usblp, /dev/usb/lp*",
        },
        "serial": {
            "available": serial_port.available(),
            "hint": "python3-serial (pyserial)",
        },
        "network": {"available": True, "hint": "TCP 9100"},
    }
