"""ENPC responder - Epson network printer discovery on UDP 3289.

Why this exists
---------------
POS apps that look for "Epson printers" use Epson's own ePOS SDK, whose
``Discovery`` class broadcasts a UDP datagram to ``255.255.255.255:3289``
starting with the ASCII magic ``EPSONQ``.  Epson's Ethernet interface for the
TM series (UB-E04) lists ENPC on UDP 3289 among its protocols, with the packet
types *Probe, Initialize, Query, Setup and Notify* - so the family is
``EPSON`` plus one letter, upper case for the request and lower case for the
matching reply (``EPSONQ`` -> ``EPSONq``, ``EPSONC`` -> ``EPSONc``).

Epson does **not** publish the payload format.  The frame layout below comes
from public reverse-engineering work:

    offset 0-5    magic, e.g. "EPSONQ"
    offset 6-9    function id (4 bytes)
    offset 10-13  payload length (4 bytes, little endian)
    offset 14+    payload

Observed discovery broadcast from the ePOS SDK, 16 bytes::

    45 50 53 4f 4e 51  03 00 00 00  10 00 00 00  00 00
    E  P  S  O  N  Q   function     length       data

Because the *reply* payload is still guesswork, BonBridge can send more than
one shape of it (``discovery.enpc_reply``):

``echo``
    Mirror the request header verbatim and append the identity.  Safe: no
    field is invented, so nothing can be wrong except the payload itself.
``epson``
    Build a proper frame with a real length field and a structured payload
    (MAC, IP, netmask, gateway, device name, model), the way a real device is
    described in the reverse-engineering write-up.
``both`` (default)
    Send both, one after the other.  A client that dislikes one usually
    ignores it and takes the other; two small datagrams cost nothing.

Every probe is written to the shared probe log with a full hexdump, so one
press of "search for printers" in the app shows exactly what arrived and
whether it was answered - see :mod:`bonbridge.probes`.

References
----------
* wes4m, "Reverse Engineering Thermal Printers" (ENPC frame layout)
  https://wes4m.io/posts/epson_rev/
* mike42/escpos-php issue #923, "Need help with ENPC protocol 3289"
  (the observed 16-byte discovery broadcast)
  https://github.com/mike42/escpos-php/issues/923
* Epson ePOS SDK, ``Discovery.start`` (the official client side)
  https://download4.epson.biz/sec_pubs/pos/reference_en/epos_and/ref_epos_sdk_and_en_discoveryclass_start.html
* Epson UB-E04 Technical Reference Guide (ENPC packet types, ports)
  https://files.support.epson.com/pdf/ube04_/ube04_trg.pdf
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

MAGIC_PREFIX = b"EPSON"

MAGIC_QUERY = b"EPSONQ"
MAGIC_QUERY_REPLY = b"EPSONq"
MAGIC_COMMAND = b"EPSONC"
MAGIC_COMMAND_REPLY = b"EPSONc"

#: The UB-E04 reference lists the packet types Probe, Initialize, Query, Setup
#: and Notify.  Rather than hard-coding a list that is probably incomplete,
#: anything of the form ``EPSON`` + one upper-case letter counts as a request
#: and is answered with the same letter in lower case.
def reply_magic(magic: bytes) -> Optional[bytes]:
    """``b"EPSONQ"`` -> ``b"EPSONq"``; ``None`` if this is not a request."""
    if len(magic) != 6 or not magic.startswith(MAGIC_PREFIX):
        return None
    letter = magic[5:6]
    if not letter.isalpha() or not letter.isupper():
        return None
    return MAGIC_PREFIX + letter.lower()


def is_request(magic: bytes) -> bool:
    return reply_magic(magic) is not None


#: Header length: 6 bytes magic + 4 bytes function + 4 bytes length field.
HEADER_LEN = 14

#: Function codes seen in captures (big-endian reading of the 4 header bytes).
FUNC_DEVICE_NAME = 0x03000000
FUNC_NETWORK_INFO = 0x03000010
FUNC_WHO_IS_HOLDING = 0x03000017

#: Which shape(s) of reply to send - see the module docstring.
REPLY_STYLES = ("echo", "epson", "both")

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


def build_structured_frame(magic: bytes, function: bytes, payload: bytes = b"") -> bytes:
    """A frame with a real length field, the way a device is expected to answer.

    ``<magic:6><function:4><len(payload):4 little endian><payload>``
    """
    return (
        magic
        + function[:4].ljust(4, b"\x00")
        + struct.pack("<I", len(payload))
        + payload
    )


def parse_frame(data: bytes) -> Optional[Dict[str, Any]]:
    """Split an ENPC datagram into magic, header tail and payload."""
    if len(data) < 6:
        return None
    magic = data[:6]
    if not (is_request(magic) or (magic.startswith(MAGIC_PREFIX) and magic[5:6].islower())):
        return None
    header_tail = data[6:HEADER_LEN].ljust(8, b"\x00")
    function = struct.unpack(">I", header_tail[:4])[0] if len(header_tail) >= 4 else 0
    return {
        "magic": magic,
        "header_tail": header_tail,
        "function_bytes": header_tail[:4],
        "function": function,
        "declared_length": struct.unpack("<I", header_tail[4:8])[0],
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
        reply_style: str = "both",
        probe_log: Optional[Any] = None,
    ):
        super().__init__(name="enpc-responder", daemon=True)
        self.device_name_provider = device_name_provider
        self.mac_provider = mac_provider
        self.ip_provider = ip_provider
        self.bind = bind
        self.port = port
        self.log_probes = log_probes
        self.model_name = model_name
        self.reply_style = reply_style if reply_style in REPLY_STYLES else "both"
        #: Shared log across all discovery protocols (bonbridge.probes.ProbeLog).
        self.probe_log = probe_log

        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
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
        while not self._stop_event.is_set():
            try:
                data, peer = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop_event.is_set():
                    log.debug("ENPC receive failed: %s", exc)
                continue
            self._handle_datagram(data, peer)

        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    # ------------------------------------------------------------------

    def _handle_datagram(self, data: bytes, peer: tuple) -> None:
        frame = parse_frame(data)
        peer_text = f"{peer[0]}:{peer[1]}"
        self.last_peer = peer_text
        recognised = frame is not None and is_request(frame["magic"])

        entry: Dict[str, Any] = {
            "time": time.time(),
            "protocol": "enpc",
            "peer": peer_text,
            "bytes": len(data),
            "hexdump": hexdump(data),
            "recognised": recognised,
            "magic": frame["magic"].decode("ascii", "replace") if frame else "",
            "function": f"0x{frame['function']:08x}" if frame else "",
            "answered": False,
            "reply_hexdump": "",
            "summary": "",
        }

        with self._lock:
            self.requests += 1

        if not recognised:
            # Not an ENPC request - could be the answer of a real printer, or
            # something else entirely.  Record it anyway: knowing what else
            # arrives on 3289 is exactly the point of this log.
            entry["summary"] = "no ENPC request"
            self._remember(entry, data)
            log.info(
                "Discovery probe from %s (not an ENPC request, %s bytes)", peer_text, len(data)
            )
            return

        assert frame is not None
        replies = self._build_replies(frame)
        entry["summary"] = f"{entry['magic']} function {entry['function']} -> {self.reply_style}"
        entry["reply_hexdump"] = "\n\n".join(hexdump(reply) for reply in replies)

        sent_to: List[str] = []
        for reply in replies:
            sent_to.extend(self._send(reply, peer))
        entry["answered"] = bool(sent_to)
        entry["reply_targets"] = sent_to
        self._remember(entry, data)

        if sent_to:
            with self._lock:
                self.replies += 1
            log.info(
                "ENPC: answered %s from %s (function %s) -> %s",
                entry["magic"],
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

    # -- reply construction ------------------------------------------------

    @staticmethod
    def _netmask_for(ip_text: str) -> bytes:
        """Netmask of the interface that carries ``ip_text``, packed."""
        from . import sysinfo

        for entry in sysinfo.ip_addresses():
            if entry.get("address") != ip_text or "/" not in (entry.get("cidr") or ""):
                continue
            try:
                bits = int(entry["cidr"].split("/", 1)[1])
                mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
                return struct.pack(">I", mask)
            except (ValueError, OSError):
                break
        return b"\xff\xff\xff\x00"

    def _identity(self) -> Dict[str, bytes]:
        from . import netwatch

        name = self.device_name_provider().encode("ascii", "replace")[:32]
        model = (self.model_name or "TM-T88V").encode("ascii", "replace")[:24]
        mac = self.mac_provider()[:6].ljust(6, b"\x00")

        def packed(address: str) -> bytes:
            try:
                return socket.inet_aton(address)
            except OSError:
                return b"\x00\x00\x00\x00"

        ip_text = self.ip_provider()
        return {
            "name": name,
            "model": model,
            "mac": mac,
            "ip": packed(ip_text),
            "netmask": self._netmask_for(ip_text),
            "gateway": packed(netwatch.default_gateway()),
        }

    def _build_replies(self, frame: Dict[str, Any]) -> List[bytes]:
        """One or two datagrams, depending on ``reply_style``."""
        magic = reply_magic(frame["magic"]) or MAGIC_QUERY_REPLY
        identity = self._identity()

        replies: List[bytes] = []
        if self.reply_style in ("echo", "both"):
            replies.append(build_frame(magic, frame["header_tail"], self._payload(frame, identity)))
        if self.reply_style in ("epson", "both"):
            payload = self._payload(frame, identity, structured=True)
            replies.append(build_structured_frame(magic, frame["function_bytes"], payload))
        return replies

    def _payload(
        self, frame: Dict[str, Any], identity: Dict[str, bytes], structured: bool = False
    ) -> bytes:
        """What goes after the header.

        The layout of a real device's reply is not published.  The structured
        variant follows the description from the reverse-engineering write-up
        (model name, MAC, IP configuration); the echo variant simply puts the
        identity where a client scanning for an ASCII model name will find it.
        """
        function = frame["function"]
        if function == FUNC_WHO_IS_HOLDING:
            # "Nobody is holding this printer" - all zeroes means free.
            return b"\x00" * 4
        if structured:
            return (
                identity["mac"]
                + identity["ip"]
                + identity["netmask"]
                + identity["gateway"]
                + identity["model"]
                + b"\x00"
                + identity["name"]
                + b"\x00"
            )
        if function == FUNC_NETWORK_INFO:
            return identity["mac"] + identity["ip"] + identity["name"] + b"\x00"
        return (
            identity["name"]
            + b"\x00"
            + identity["model"]
            + b"\x00"
            + identity["mac"]
            + identity["ip"]
        )

    def _remember(self, entry: Dict[str, Any], data: bytes = b"") -> None:
        # The shared log is what the diagnostics page shows across all
        # protocols; the local list keeps the ENPC-only view working.
        # `data` stays out of `entry` on purpose - the entry is serialised to
        # JSON for the web interface, and raw bytes are not JSON.
        if self.probe_log is not None:
            self.probe_log.add(
                "enpc",
                entry["peer"],
                data,
                answered=entry["answered"],
                summary=entry.get("summary", ""),
            )
        if not self.log_probes:
            return
        with self._lock:
            self.probes.insert(0, entry)
            del self.probes[PROBE_LOG_SIZE:]

    # ------------------------------------------------------------------

    def stop(self) -> None:
        self._stop_event.set()

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
