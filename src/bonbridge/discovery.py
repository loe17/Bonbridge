"""Experimental ENPC responder (Epson network discovery, UDP 3289).

Background
----------
The OrderAssist app has a "search for printers" button.  Its own
documentation says the search "may return no results if no EPSON printer is
used" - i.e. discovery is Epson specific.  Epson devices are found with the
ENPC protocol: the client broadcasts a UDP datagram to port 3289 that starts
with the ASCII magic ``EPSONQ``, and Epson devices answer with ``EPSONq``.

BonBridge can answer those probes so the bridge shows up in the app's printer
search instead of having to be typed in by hand.

**This module is experimental and disabled by default.**  Epson does not
publish the ENPC specification; the frame layout implemented here was derived
from community reverse-engineering work and has not been verified against
every app version.  Manual entry of the IP address is and remains the
supported path - see docs/*/04-orderassist.md.

Enable with ``discovery.enpc: true`` in the configuration.
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger(__name__)

ENPC_PORT = 3289
MAGIC_QUERY = b"EPSONQ"
MAGIC_QUERY_REPLY = b"EPSONq"
MAGIC_COMMAND = b"EPSONC"
MAGIC_COMMAND_REPLY = b"EPSONc"

#: Known function codes (4 bytes, big endian) seen in captures.
FUNC_BROADCAST_DISCOVERY = 0x00000000
FUNC_NETWORK_INFO = 0x03000010
FUNC_DEVICE_NAME = 0x03000000
FUNC_WHO_IS_HOLDING = 0x03000017


def build_frame(magic: bytes, function: int, payload: bytes = b"") -> bytes:
    """``<magic:6><function:4><length:4><payload>``."""
    return magic + struct.pack(">II", function, len(payload)) + payload


def parse_frame(data: bytes) -> Optional[Dict[str, Any]]:
    if len(data) < 14:
        return None
    magic = data[:6]
    if magic not in (MAGIC_QUERY, MAGIC_COMMAND, MAGIC_QUERY_REPLY, MAGIC_COMMAND_REPLY):
        return None
    function, length = struct.unpack(">II", data[6:14])
    payload = data[14 : 14 + length]
    return {"magic": magic, "function": function, "length": length, "payload": payload}


class EnpcResponder(threading.Thread):
    """Answer ENPC discovery probes on UDP 3289."""

    def __init__(
        self,
        device_name_provider: Callable[[], str],
        mac_provider: Callable[[], bytes],
        ip_provider: Callable[[], str],
        bind: str = "0.0.0.0",
        port: int = ENPC_PORT,
    ):
        super().__init__(name="enpc-responder", daemon=True)
        self.device_name_provider = device_name_provider
        self.mac_provider = mac_provider
        self.ip_provider = ip_provider
        self.bind = bind
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._stop = threading.Event()
        self.requests = 0
        self.last_peer = ""
        self.last_error: Optional[str] = None

    def run(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                pass
            self._sock.bind((self.bind, self.port))
            self._sock.settimeout(0.5)
        except OSError as exc:
            self.last_error = str(exc)
            log.warning("ENPC responder cannot bind %s:%s: %s", self.bind, self.port, exc)
            return

        log.info("ENPC responder listening on %s:%s (experimental)", self.bind, self.port)
        while not self._stop.is_set():
            try:
                data, peer = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop.is_set():
                    log.debug("ENPC receive failed: %s", exc)
                continue

            frame = parse_frame(data)
            if frame is None or frame["magic"] != MAGIC_QUERY:
                continue
            self.requests += 1
            self.last_peer = f"{peer[0]}:{peer[1]}"
            reply = self._build_reply(frame)
            if reply:
                try:
                    self._sock.sendto(reply, peer)
                    log.info("ENPC: answered discovery from %s", self.last_peer)
                except OSError as exc:
                    log.debug("ENPC reply failed: %s", exc)

        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    def _build_reply(self, frame: Dict[str, Any]) -> bytes:
        function = frame["function"]
        name = self.device_name_provider().encode("ascii", "replace")[:32]
        if function in (FUNC_BROADCAST_DISCOVERY, FUNC_DEVICE_NAME):
            return build_frame(MAGIC_QUERY_REPLY, function, name + b"\x00")
        if function == FUNC_NETWORK_INFO:
            mac = self.mac_provider()[:6].ljust(6, b"\x00")
            try:
                ip = socket.inet_aton(self.ip_provider())
            except OSError:
                ip = b"\x00\x00\x00\x00"
            payload = mac + ip + name + b"\x00"
            return build_frame(MAGIC_QUERY_REPLY, function, payload)
        if function == FUNC_WHO_IS_HOLDING:
            return build_frame(MAGIC_QUERY_REPLY, function, b"\x00" * 4)
        # Unknown function: answer with an empty payload rather than staying
        # silent, so the client at least sees the device.
        return build_frame(MAGIC_QUERY_REPLY, function, b"")

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "port": self.port,
            "requests": self.requests,
            "last_peer": self.last_peer,
            "error": self.last_error,
            "experimental": True,
        }


def local_mac(interface_hint: str = "") -> bytes:
    """Read a MAC address from sysfs (used for the ENPC network info reply)."""
    import glob
    import os

    candidates: List[str] = []
    if interface_hint:
        candidates.append(f"/sys/class/net/{interface_hint}/address")
    candidates.extend(sorted(glob.glob("/sys/class/net/*/address")))
    for path in candidates:
        name = os.path.basename(os.path.dirname(path))
        if name == "lo":
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read().strip()
            parts = text.split(":")
            if len(parts) == 6:
                return bytes(int(p, 16) for p in parts)
        except (OSError, ValueError):
            continue
    return b"\x00" * 6
