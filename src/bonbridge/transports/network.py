"""Network transport (RAW / JetDirect, TCP 9100).

Used when the printer already has an Ethernet or Wi-Fi interface (Epson
UB-E04 / UB-R04, TM-m30III, most generic Wi-Fi POS printers).  In that case
BonBridge is not strictly required to print at all - but it is still useful
as a monitoring and diagnostics gateway, and it lets one bridge serve a mix
of USB and network printers under one web interface.
"""

from __future__ import annotations

import logging
import socket
from typing import Any, Dict, Optional

from .base import BaseTransport, TransportError

log = logging.getLogger(__name__)

DEFAULT_PORT = 9100


def available() -> bool:
    return True


class NetworkTransport(BaseTransport):
    """Persistent TCP connection to a RAW/JetDirect printer."""

    type_name = "network"
    bidirectional = True

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        super().__init__(settings)
        self._sock: Optional[socket.socket] = None
        # Bytes read while checking whether the connection is still alive.
        # They are handed to the next read() instead of being dropped.
        self._rx = bytearray()

    @property
    def host(self) -> str:
        return (self.settings.get("host") or "").strip()

    @property
    def port(self) -> int:
        try:
            return int(self.settings.get("port") or DEFAULT_PORT)
        except (TypeError, ValueError):
            return DEFAULT_PORT

    def open(self) -> None:
        with self._lock:
            if self._open:
                return
            if not self.host:
                raise TransportError("No host configured for the network transport")
            timeout = float(self.settings.get("connect_timeout") or 5.0)
            try:
                self._sock = socket.create_connection((self.host, self.port), timeout=timeout)
                self._sock.settimeout(float(self.settings.get("io_timeout") or 10.0))
                try:
                    self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                except OSError:
                    pass
            except OSError as exc:
                self._sock = None
                raise TransportError(f"Cannot connect to {self.host}:{self.port}: {exc}") from exc
            self._open = True
            log.info("Network printer opened: %s:%s", self.host, self.port)

    def close(self) -> None:
        with self._lock:
            self._open = False
            self._rx.clear()
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None

    def _check_alive(self) -> None:
        """Detect a half-closed connection before writing into a black hole.

        A plain ``sendall`` on a socket the peer has already closed succeeds
        (the data lands in the kernel buffer and the RST arrives later), which
        would make BonBridge report a job as printed although the printer
        never saw it.  A non-blocking read tells us the truth; any real data
        we pick up on the way is buffered for the next ``read()``.
        """
        sock = self._sock
        if sock is None:
            raise TransportError("not connected")
        previous = sock.gettimeout()
        try:
            sock.settimeout(0)
            while True:
                try:
                    chunk = sock.recv(4096)
                except (BlockingIOError, InterruptedError):
                    return  # nothing pending: connection is healthy
                except socket.timeout:
                    return
                except OSError as exc:
                    raise TransportError(f"connection to {self.host}:{self.port} lost: {exc}") from exc
                if not chunk:
                    raise TransportError(
                        f"printer at {self.host}:{self.port} closed the connection"
                    )
                self._rx.extend(chunk)
                if len(self._rx) > 4096:
                    del self._rx[:-4096]
        finally:
            try:
                sock.settimeout(previous)
            except OSError:
                pass

    def write(self, data: bytes) -> int:
        if not data:
            return 0
        with self._lock:
            if not self._open:
                self.open()
            assert self._sock is not None
            try:
                self._check_alive()
                self._sock.sendall(data)
                return len(data)
            except TransportError:
                self.close()
                raise
            except OSError as exc:
                self.close()
                raise TransportError(f"Network write to {self.host}:{self.port} failed: {exc}") from exc

    def read(self, size: int = 64, timeout: float = 1.0) -> bytes:
        with self._lock:
            if self._rx:
                chunk = bytes(self._rx[:size])
                del self._rx[: len(chunk)]
                return chunk
            if not self._open or self._sock is None:
                return b""
            previous = self._sock.gettimeout()
            try:
                self._sock.settimeout(timeout)
                return self._sock.recv(size)
            except socket.timeout:
                return b""
            except OSError as exc:
                log.debug("Network read failed: %s", exc)
                return b""
            finally:
                try:
                    self._sock.settimeout(previous)
                except OSError:
                    pass

    def connection_label(self) -> str:
        return f"{self.host}:{self.port}"
