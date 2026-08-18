"""ENPC responder - Epson network printer discovery on UDP 3289.

Why this exists
---------------
The OrderAssist app has a "search for printers" button.  Its own documentation
says the search "may return no results if no EPSON printer is used", i.e. the
search is Epson specific.  Epson's ePOS SDK finds devices by broadcasting a
UDP datagram to port 3289 whose payload starts with the ASCII magic
``EPSONQ``; devices answer with ``EPSONq``.

Epson does **not** publish the ENPC specification.  Everything below is derived
from public reverse-engineering work, so the reply is *best effort*: BonBridge
echoes the request header back with the lower-case magic and appends the
device identity.  Answering costs nothing and cannot break anything - the
worst case is that the app ignores the reply and the printer still has to be
added by IP address, which is the documented and supported path.

To make this verifiable instead of guesswork, every probe is recorded with a
full hexdump (``discovery.log_probes``) and shown in the web interface under
*Diagnostics -> Discovery*.  That answers the decisive question in one test
run: **does the app send anything to port 3289 at all?**

* If probes appear, the transport works and only the reply format is in
  question - the hexdump tells us what to change.
* If no probes appear, the app does not use ENPC and the search must work some
  other way; no reply format would ever have helped.

Observed request (from the escpos-php issue linked below), 16 bytes:

    45 50 53 4f 4e 51  03 00 00 00  10 00 00 00  00 00
    E  P  S  O  N  Q   <-- header, echoed back verbatim -->

References
----------
* wes4m, "Reverse Engineering Thermal Printers"
  https://wes4m.io/posts/epson_rev/
* mike42/escpos-php issue #923, "Need help with ENPC protocol 3289"
  https://github.com/mike42/escpos-php/issues/923
* Epson ePOS SDK, ``Discovery.start`` (the official client side)
  https://download4.epson.biz/sec_pubs/pos/reference_en/epos_and/ref_epos_sdk_and_en_discoveryclass_start.html
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger(__name__)

ENPC_PORT = 3289

MAGIC_QUERY = b"EPSONQ"
MAGIC_QUERY_REPLY = b"EPSONq"
MAGIC_COMMAND = b"EPSONC"
MAGIC_COMMAND_REPLY = b"EPSONc"

QUERY_MAGICS = (MAGIC_QUERY, MAGIC_COMMAND)
REPLY_FOR = {MAGIC_QUERY: MAGIC_QUERY_REPLY, MAGIC_COMMAND: MAGIC_COMMAND_REPLY}

#: Header length: 6 bytes magic + 4 bytes function + 4 bytes length field.
HEADER_LEN = 14

#: Function codes seen in captures (big-endian reading of the 4 header bytes).
FUNC_DEVICE_NAME = 0x03000000
FUNC_NETWORK_INFO = 0x03000010
FUNC_WHO_IS_HOLDING = 0x03000017

#: How many probes to keep for the diagnostics page.
PROBE_LOG_SIZE = 40


def hexdump(data: bytes, width: int = 16) -> str:
    """Classic offset / hex / ASCII dump, used in the diagnostics view."""
    lines: List[str] = []
    for offset in range(0, len(data), width):
        chunk = data[offset : offset + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(width * 3 - 1)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:04x}  {hex_part}  |{text}|")
    return "\n".join(lines)


def build_frame(magic: bytes, header_tail: bytes, payload: bytes = b"") -> bytes:
    """``<magic:6><header_tail:8><payload>``.

    ``header_tail`` is echoed from the request so we do not have to guess the
    function/length encoding.
    """
    return magic + header_tail[:8].ljust(8, b"\x00") + payload


def parse_frame(data: bytes) -> Optional[Dict[str, Any]]:
    """Split an ENPC datagram into magic, header tail and payload."""
    if len(data) < 6:
        return None
    magic = data[:6]
    if magic not in (MAGIC_QUERY, MAGIC_COMMAND, MAGIC_QUERY_REPLY, MAGIC_COMMAND_REPLY):
        return None
    header_tail = data[6:HEADER_LEN].ljust(8, b"\x00")
    function = struct.unpack(">I", header_tail[:4])[0] if len(header_tail) >= 4 else 0
    return {
        "magic": magic,
        "header_tail": header_tail,
        "function": function,
        "payload": data[HEADER_LEN:],
        "raw": data,
    }


class EnpcResponder(threading.Thread):
    """Answer (and record) Epson discovery probes on UDP 3289."""

    def __init__(
        self,
        device_name_provider: Callable[[], str],
        mac_provider: Callable[[], bytes],
        ip_provider: Callable[[], str],
        bind: str = "0.0.0.0",
        port: int = ENPC_PORT,
        log_probes: bool = True,
        model_name: str = "TM-T88V",
    ):
        super().__init__(name="enpc-responder", daemon=True)
        self.device_name_provider = device_name_provider
        self.mac_provider = mac_provider
        self.ip_provider = ip_provider
        self.bind = bind
        self.port = port
        self.log_probes = log_probes
        self.model_name = model_name

        self._sock: Optional[socket.socket] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._local_cache: Optional[set] = None

        self.requests = 0
        self.replies = 0
        self.last_peer = ""
        self.last_error: Optional[str] = None
        self.probes: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------

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

        log.info("ENPC discovery responder listening on %s:%s", self.bind, self.port)
        while not self._stop.is_set():
            try:
                data, peer = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop.is_set():
                    log.debug("ENPC receive failed: %s", exc)
                continue
            self._handle(data, peer)

        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    # ------------------------------------------------------------------

    def _handle(self, data: bytes, peer: tuple) -> None:
        frame = parse_frame(data)
        peer_text = f"{peer[0]}:{peer[1]}"
        self.last_peer = peer_text

        entry: Dict[str, Any] = {
            "time": time.time(),
            "peer": peer_text,
            "bytes": len(data),
            "hexdump": hexdump(data),
            "recognised": frame is not None and frame["magic"] in QUERY_MAGICS,
            "magic": frame["magic"].decode("ascii", "replace") if frame else "",
            "function": f"0x{frame['function']:08x}" if frame else "",
            "answered": False,
            "reply_hexdump": "",
        }

        with self._lock:
            self.requests += 1

        if frame is None or frame["magic"] not in QUERY_MAGICS:
            # Not an ENPC query (could be an answer from a real printer, or
            # something else entirely).  Record it anyway - knowing what else
            # arrives on 3289 is exactly the point of this log.
            self._remember(entry)
            log.info("Discovery probe from %s (not an ENPC query, %s bytes)", peer_text, len(data))
            return

        reply = self._build_reply(frame)
        entry["reply_hexdump"] = hexdump(reply)
        sent_to = self._send(reply, peer)
        entry["answered"] = bool(sent_to)
        entry["reply_targets"] = sent_to
        self._remember(entry)

        if sent_to:
            with self._lock:
                self.replies += 1
            log.info(
                "ENPC: answered discovery probe from %s (function %s) -> %s",
                peer_text,
                entry["function"],
                ", ".join(sent_to),
            )

    def _local_addresses(self) -> set:
        """Our own IPv4 addresses - used to avoid answering ourselves."""
        if self._local_cache is None:
            from . import sysinfo

            addresses = {"127.0.0.1", "0.0.0.0"}
            try:
                for entry in sysinfo.ip_addresses():
                    if entry.get("family") == "ipv4":
                        addresses.add(entry["address"])
            except Exception:  # noqa: BLE001
                pass
            self._local_cache = addresses
        return self._local_cache

    def _send(self, reply: bytes, peer: tuple) -> List[str]:
        """Answer the source port *and* port 3289.

        Some clients broadcast from an ephemeral port but listen for the answer
        on 3289 instead.  Sending to both costs one extra datagram and removes a
        whole class of "no devices found" failures.  The second datagram is
        skipped when the peer is this machine, otherwise we would answer our
        own socket and clutter the probe log.
        """
        targets = []
        candidates = [(peer[0], peer[1])]
        if peer[1] != self.port and peer[0] not in self._local_addresses():
            candidates.append((peer[0], self.port))
        for address in candidates:
            try:
                assert self._sock is not None
                self._sock.sendto(reply, address)
                targets.append(f"{address[0]}:{address[1]}")
            except OSError as exc:
                log.debug("ENPC reply to %s failed: %s", address, exc)
        return targets

    def _build_reply(self, frame: Dict[str, Any]) -> bytes:
        """Echo the request header, append identity as the payload.

        Echoing means we do not have to know whether the four header bytes
        after the magic are a function code, a length, or both - whatever the
        client sent, it gets back.
        """
        magic = REPLY_FOR.get(frame["magic"], MAGIC_QUERY_REPLY)
        name = self.device_name_provider().encode("ascii", "replace")[:32]
        mac = self.mac_provider()[:6].ljust(6, b"\x00")
        try:
            ip = socket.inet_aton(self.ip_provider())
        except OSError:
            ip = b"\x00\x00\x00\x00"

        function = frame["function"]
        if function == FUNC_NETWORK_INFO:
            payload = mac + ip + name + b"\x00"
        elif function == FUNC_WHO_IS_HOLDING:
            payload = b"\x00" * 4
        else:
            # Device name / broadcast discovery and anything unknown: identify
            # ourselves with name, MAC and IP.  Extra bytes are ignored by
            # clients that only want the name.
            payload = name + b"\x00" + mac + ip

        return build_frame(magic, frame["header_tail"], payload)

    def _remember(self, entry: Dict[str, Any]) -> None:
        if not self.log_probes:
            return
        with self._lock:
            self.probes.insert(0, entry)
            del self.probes[PROBE_LOG_SIZE:]

    # ------------------------------------------------------------------

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": True,
                "port": self.port,
                "listening": self._sock is not None and self.last_error is None,
                "requests": self.requests,
                "replies": self.replies,
                "last_peer": self.last_peer,
                "error": self.last_error,
                "probes": list(self.probes),
                "note_de": (
                    "Epson veroeffentlicht das Suchprotokoll nicht. Wenn hier Anfragen "
                    "auftauchen, erreicht die Suche das Geraet - dann laesst sich das "
                    "Antwortformat anhand des Hexdumps nachziehen. Wenn hier nichts "
                    "auftaucht, benutzt die App kein ENPC und der manuelle Weg ueber die "
                    "IP-Adresse bleibt der richtige."
                ),
                "note_en": (
                    "Epson does not publish the discovery protocol. If probes show up "
                    "here the search reaches the device and the reply format can be "
                    "corrected from the hexdump. If nothing shows up the app does not "
                    "use ENPC and adding the printer by IP remains the way to go."
                ),
            }

    def clear_probes(self) -> int:
        with self._lock:
            count = len(self.probes)
            self.probes = []
            return count


def local_mac(interface_hint: str = "") -> bytes:
    """Read a MAC address from sysfs (used in the ENPC network info reply)."""
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
