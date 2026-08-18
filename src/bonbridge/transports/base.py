"""Common transport interface.

A transport owns the physical connection to exactly one printer.  Only the
printer worker touches it, which is what guarantees that print jobs never
interleave (the main flaw of the previous ``socat``/CUPS setup, where both
wrote to ``/dev/usb/lp0`` at the same time).

Every transport is expected to be *bidirectional* where the hardware allows
it: ``read()`` is what makes paper/cover/error status available at all.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)


class TransportError(RuntimeError):
    """Raised when the printer connection fails or is unavailable."""


class BaseTransport:
    """Abstract base class for all printer transports."""

    #: Short type name used in the configuration file.
    type_name = "base"

    #: ``True`` when the transport can read data back from the printer.
    bidirectional = False

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self.settings: Dict[str, Any] = dict(settings or {})
        self._lock = threading.RLock()
        self._open = False

    # -- lifecycle ---------------------------------------------------------

    def open(self) -> None:
        """Open the connection.  Raises :class:`TransportError` on failure."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the connection.  Must never raise."""
        raise NotImplementedError

    @property
    def is_open(self) -> bool:
        return self._open

    def reopen(self) -> None:
        self.close()
        self.open()

    # -- I/O ---------------------------------------------------------------

    def write(self, data: bytes) -> int:
        """Write raw bytes to the printer, returning the number written."""
        raise NotImplementedError

    def read(self, size: int = 64, timeout: float = 1.0) -> bytes:
        """Read up to ``size`` bytes.  Returns ``b""`` when unsupported."""
        return b""

    def drain(self, timeout: float = 0.2) -> bytes:
        """Read and discard whatever the printer has queued up."""
        if not self.bidirectional:
            return b""
        try:
            return self.read(256, timeout)
        except TransportError:
            return b""

    # -- description -------------------------------------------------------

    def describe(self) -> Dict[str, Any]:
        """Human readable description shown in the web interface."""
        return {
            "type": self.type_name,
            "bidirectional": self.bidirectional,
            "open": self.is_open,
            "settings": {k: v for k, v in self.settings.items() if k != "password"},
        }

    def connection_label(self) -> str:
        return self.type_name

    def __enter__(self) -> "BaseTransport":
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
