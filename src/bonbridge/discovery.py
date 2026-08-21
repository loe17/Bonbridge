"""ENPC responder - Epson network printer discovery on UDP 3289.

What is known, and how
----------------------
Epson does not publish ENPC.  Everything here rests on two things: public
reverse-engineering of a real TM-m30, and a capture taken from the actual POS
app on the actual network this runs on.

**The request the app sends** (captured 2026-08-21, repeated every ~3 s from
the same source port until something is accepted), 14 bytes::

    45 50 53 4f 4e 51  03 00 00 00  00 00 00 00
    E  P  S  O  N  Q   function     length = 0

**The reply of a real TM-m30** to the same function, 147 bytes::

    45 50 53 4f 4e 71  03 00 00 00  00 00 00 85  00 05 01 02 01
    E  P  S  O  N  q   function     length = 133  "TM-m30" + NUL padding

and its network-info reply, 37 bytes::

    45 50 53 4f 4e 71  00 00 00 10  00 00 00 17
    01 02 00 00 00 00     MAC
    00 00 04              (unknown)
    c0 a8 01 09           IP       192.168.1.9
    ff ff ff 00           netmask  255.255.255.0
    c0 a8 01 01           gateway  192.168.1.1
    80 7c                 (unknown)

Two facts fall out of that, and neither is a guess:

1. **The length field is big endian.**  ``00 00 00 17`` is followed by exactly
   23 payload bytes; read little endian the same field would be 385 875 968.
2. **Mirroring the request header cannot work.**  The request declares a
   payload length of *zero*, so a reply that echoes that header and then
   appends data is telling the client "there is nothing here" - and a parser
   that trusts the length field stops reading.  That was the previous default
   behaviour, and it explains the silence.

What is still unknown is the meaning of the five bytes ``00 05 01 02 01`` in
front of the model name.  Rather than pick one interpretation and call it
settled, this module keeps a list of candidate reply layouts (see
:data:`REPLY_CANDIDATES`) - the first of which simply reproduces the captured
device reply byte for byte with the model name swapped.

Turning the app's own impatience into a search
----------------------------------------------
The app re-broadcasts every three seconds until it is satisfied.  That is a
free format search: in ``cycle`` mode each retry is answered with the *next*
candidate, and the probe log names the candidate used for each one.  A single
press of "search for printers" therefore tries every layout, and whichever one
was in flight when the printer appeared is the one that is right.

References
----------
* wes4m, "Reverse Engineering Thermal Printers" - frame layout and the
  captured TM-m30 replies reproduced above
  https://wes4m.io/posts/epson_rev/
* mike42/escpos-php issue #923, "Need help with ENPC protocol 3289"
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
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

ENPC_PORT = 3289

#: ``IP_PKTINFO`` from ``<linux/in.h>``.  Python does not export the constant on
#: every build, so the numeric value is used as a fallback - guarded by a
#: platform check, because 8 means something else on BSD and macOS.
IP_PKTINFO = getattr(socket, "IP_PKTINFO", 8 if sys.platform.startswith("linux") else None)

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


#: Header length: everything before the payload.
HEADER_LEN = 14

#: Device type byte (offset 6).  The searching app asks the *printer* for its
#: name and the *network interface* for its addresses - two different values.
DEVICE_TYPE_NETWORK = 0x00
DEVICE_TYPE_PRINTER = 0x03

#: Function (offset 8-9, big endian 16 bit).
FUNC_BASIC_INFO = 0x0000
FUNC_STATUS = 0x0010
FUNC_FORCED_TRANSMISSION = 0x0011
FUNC_RESET = 0x0012
FUNC_BUFFER_FLASH = 0x0013
FUNC_CLEAR_TIMEOUT = 0x0016
FUNC_WHO_IS_HOLDING = 0x0017

FUNCTION_NAMES = {
    FUNC_BASIC_INFO: "Basisinformation / basic information",
    FUNC_STATUS: "Status",
    FUNC_FORCED_TRANSMISSION: "Forced transmission",
    FUNC_RESET: "Reset",
    FUNC_BUFFER_FLASH: "Buffer flash",
    FUNC_CLEAR_TIMEOUT: "Clear connection timeout",
    FUNC_WHO_IS_HOLDING: "Wer belegt den Drucker / who is holding",
}

#: Result code (offset 10-11, big endian 16 bit).  Replies only; always zero in
#: a request.
RESULT_OK = 0x0000
RESULT_NO_DEVICE = 0xFFFE
RESULT_UNSUPPORTED = 0xFFFF

#: Fixed blobs from the captured device.  Their meaning is not published, and
#: inventing values here would be worse than replaying what a real printer
#: demonstrably sends.
PREFIX_DEVICE_NAME = b"\x00\x05\x01\x02\x01"
NAME_FIELD_LEN = 128  # 5 + 128 = 133 = the captured payload length
DEVICE_INFO_BLOB = bytes.fromhex("0e14 0000 0fff ffff ff39 4140 00".replace(" ", ""))
NETWORK_TAIL = b"\x80\x7c"
INTERFACE_NAME_LEN = 33
INTERFACE_TAIL = bytes.fromhex("01ffff15000200")
INTERFACE_SUFFIX = bytes.fromhex("00000001") + bytes.fromhex("00000001")

#: The interface name from the capture.  Used verbatim by one candidate.
CAPTURED_INTERFACE_NAME = b"UB-EEAE083ENSN"

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


def build_reply(
    magic: bytes,
    device_type: int,
    device_number: int,
    function: int,
    payload: bytes = b"",
    result: int = RESULT_OK,
) -> bytes:
    """Assemble a reply with every header field in its documented place."""
    return (
        magic
        + bytes((device_type & 0xFF, device_number & 0xFF))
        + struct.pack(">H", function & 0xFFFF)
        + struct.pack(">H", result & 0xFFFF)
        + struct.pack(">H", len(payload))
        + payload
    )


def build_echo_frame(magic: bytes, header_tail: bytes, payload: bytes = b"") -> bytes:
    """Mirror the request header verbatim and append a payload.

    Kept only so the old behaviour can still be selected for comparison.  It is
    structurally broken: the request declares a payload length of zero, so a
    parser that trusts the length field never looks at the payload.
    """
    return magic + header_tail[:8].ljust(8, b"\x00") + payload


def parse_frame(data: bytes) -> Optional[Dict[str, Any]]:
    """Split an ENPC datagram into its header fields and payload."""
    if len(data) < 6:
        return None
    magic = data[:6]
    if not (is_request(magic) or (magic.startswith(MAGIC_PREFIX) and magic[5:6].islower())):
        return None
    header = data[6:HEADER_LEN].ljust(8, b"\x00")
    function = struct.unpack(">H", header[2:4])[0]
    return {
        "magic": magic,
        "header_tail": header,
        "device_type": header[0],
        "device_number": header[1],
        "function": function,
        "function_name": FUNCTION_NAMES.get(function, "unbekannt / unknown"),
        "result": struct.unpack(">H", header[4:6])[0],
        "declared_length": struct.unpack(">H", header[6:8])[0],
        "payload": data[HEADER_LEN:],
        "raw": data,
    }


def describe_frame(frame: Dict[str, Any]) -> str:
    """One line for the probe log, in the protocol's own vocabulary."""
    kind = {DEVICE_TYPE_PRINTER: "Drucker/printer", DEVICE_TYPE_NETWORK: "Netzwerk/network"}.get(
        frame["device_type"], f"0x{frame['device_type']:02x}"
    )
    return (
        f"{frame['magic'].decode('ascii', 'replace')} "
        f"Geraetetyp {kind} "
        f"Funktion 0x{frame['function']:04x} ({frame['function_name']})"
    )


# --------------------------------------------------------------------------
# The payloads a real device sends, per (device type, function)
# --------------------------------------------------------------------------


def payload_device_name(model: bytes) -> bytes:
    """Printer basic information: the model name in a fixed 128-byte field."""
    return PREFIX_DEVICE_NAME + model[: NAME_FIELD_LEN - 1].ljust(NAME_FIELD_LEN, b"\x00")


def payload_interface_info(interface_name: bytes, mac: bytes) -> bytes:
    """Network interface basic information (the broadcast query)."""
    return (
        interface_name[: INTERFACE_NAME_LEN - 1].ljust(INTERFACE_NAME_LEN, b"\x00")
        + INTERFACE_TAIL
        + mac
        + INTERFACE_SUFFIX
    )


def payload_network_info(identity: Dict[str, bytes]) -> bytes:
    """Network interface status: MAC and the IP configuration."""
    return (
        b"\x01"
        + identity["mac"]
        + b"\x00\x04"
        + identity["ip"]
        + identity["netmask"]
        + identity["gateway"]
        + NETWORK_TAIL
    )


def payload_printer_info() -> bytes:
    """Printer status blob.  Replayed verbatim; the fields are not published."""
    return DEVICE_INFO_BLOB


def emulator_reply(
    frame: Dict[str, Any],
    magic: bytes,
    identity: Dict[str, bytes],
    interface_name: bytes,
) -> List[bytes]:
    """Answer exactly the query that was asked, the way a TM-m30 answers it.

    Every branch corresponds to one captured request/response pair.  A query we
    have no template for is answered honestly with "function not supported"
    rather than with a plausible-looking invention - a wrong answer is worse
    than an admitted gap, because the client believes it.
    """
    device_type = frame["device_type"]
    function = frame["function"]

    def reply(payload: bytes, result: int = RESULT_OK) -> List[bytes]:
        return [build_reply(magic, device_type, frame["device_number"], function, payload, result)]

    if function == FUNC_BASIC_INFO:
        if device_type == DEVICE_TYPE_NETWORK:
            return reply(payload_interface_info(interface_name, identity["mac"]))
        return reply(payload_device_name(identity["model"]))
    if function == FUNC_STATUS:
        if device_type == DEVICE_TYPE_NETWORK:
            return reply(payload_network_info(identity))
        return reply(payload_printer_info())
    if function == FUNC_WHO_IS_HOLDING:
        # All zeroes: nobody is holding this printer, it is free to use.
        return reply(b"\x00" * 4)
    return reply(b"", RESULT_UNSUPPORTED)


# --------------------------------------------------------------------------
# Candidate reply layouts
# --------------------------------------------------------------------------


def _generated_interface_name(mac: bytes) -> bytes:
    """An interface name shaped like the captured one, built from our MAC."""
    return b"UB-" + mac.hex()[-7:].upper().encode("ascii") + b"ENSN"


def _c_emulator(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return emulator_reply(frame, magic, identity, _generated_interface_name(identity["mac"]))


def _c_emulator_literal(
    frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]
) -> List[bytes]:
    return emulator_reply(frame, magic, identity, CAPTURED_INTERFACE_NAME)


def _c_emulator_all(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    """The asked-for reply plus the other three, unprompted.

    For clients that expect to learn name *and* addresses before they list a
    device but only ever send one query.
    """
    name = _generated_interface_name(identity["mac"])
    out = emulator_reply(frame, magic, identity, name)
    extras = [
        (DEVICE_TYPE_PRINTER, FUNC_BASIC_INFO, payload_device_name(identity["model"])),
        (DEVICE_TYPE_NETWORK, FUNC_BASIC_INFO, payload_interface_info(name, identity["mac"])),
        (DEVICE_TYPE_NETWORK, FUNC_STATUS, payload_network_info(identity)),
        (DEVICE_TYPE_PRINTER, FUNC_STATUS, payload_printer_info()),
    ]
    for device_type, function, payload in extras:
        if device_type == frame["device_type"] and function == frame["function"]:
            continue  # already sent as the direct answer
        out.append(build_reply(magic, device_type, frame["device_number"], function, payload))
    return out


def _c_name_padded(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    payload = identity["model"][:132].ljust(133, b"\x00")
    return [
        build_reply(
            magic, frame["device_type"], frame["device_number"], frame["function"], payload
        )
    ]


def _c_name_plain(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return [
        build_reply(
            magic,
            frame["device_type"],
            frame["device_number"],
            frame["function"],
            identity["model"] + b"\x00",
        )
    ]


def _c_identity(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    payload = (
        identity["mac"]
        + identity["ip"]
        + identity["netmask"]
        + identity["gateway"]
        + identity["model"]
        + b"\x00"
        + identity["name"]
        + b"\x00"
    )
    return [
        build_reply(
            magic, frame["device_type"], frame["device_number"], frame["function"], payload
        )
    ]


def _c_legacy_echo(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    payload = (
        identity["name"] + b"\x00" + identity["model"] + b"\x00" + identity["mac"] + identity["ip"]
    )
    return [build_echo_frame(magic, frame["header_tail"], payload)]


REPLY_CANDIDATES: List[Dict[str, Any]] = [
    {
        "id": "emulator",
        "de": "Vollstaendig: jede Anfrage wird so beantwortet wie von einem echten TM-m30",
        "en": "Complete: every query answered the way a real TM-m30 answers it",
        "builder": _c_emulator,
    },
    {
        "id": "emulator+all",
        "de": "Wie 'emulator', schickt zusaetzlich Name, Adressen und Status unaufgefordert mit",
        "en": "Like 'emulator' plus name, addresses and status sent unprompted",
        "builder": _c_emulator_all,
    },
    {
        "id": "emulator-literal",
        "de": "Wie 'emulator', aber mit dem Schnittstellennamen aus dem Originalmitschnitt",
        "en": "Like 'emulator' but with the interface name from the original capture",
        "builder": _c_emulator_literal,
    },
    {
        "id": "name-padded",
        "de": "Nur der Modellname, auf 133 Byte mit Nullen aufgefuellt, ohne Praefix",
        "en": "Just the model name, NUL-padded to 133 bytes, without the prefix",
        "builder": _c_name_padded,
    },
    {
        "id": "name-plain",
        "de": "Nur der Modellname mit abschliessender Null, keine Auffuellung",
        "en": "Just the model name with a terminating NUL, no padding",
        "builder": _c_name_plain,
    },
    {
        "id": "identity",
        "de": "MAC, IP, Maske, Gateway, Modell, Geraetename am Stueck",
        "en": "MAC, IP, netmask, gateway, model, device name in one block",
        "builder": _c_identity,
    },
    {
        "id": "legacy-echo",
        "de": "Alte Fassung: Anfrage-Kopf gespiegelt (Laengenfeld bleibt 0 - nachweislich falsch)",
        "en": "Old behaviour: request header mirrored (length stays 0 - demonstrably wrong)",
        "builder": _c_legacy_echo,
    },
]

CANDIDATE_IDS = [entry["id"] for entry in REPLY_CANDIDATES]

#: ``cycle`` walks the list, one candidate per probe.  Any candidate id pins
#: that one layout.  ``all`` sends every candidate at once - noisy, but useful
#: when a client only ever sends a single probe.
REPLY_STYLES = ("cycle", "all", *CANDIDATE_IDS)


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
        self.reply_style = reply_style if reply_style in REPLY_STYLES else "cycle"
        #: Shared log across all discovery protocols (bonbridge.probes.ProbeLog).
        self.probe_log = probe_log

        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._local_cache: Optional[set] = None
        #: Position in REPLY_CANDIDATES per peer, for ``cycle`` mode.
        self._cycle: Dict[str, int] = {}
        self._pktinfo = False
        self.last_candidate = ""
        self.last_local = ""

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
            # Ask the kernel to tell us *which* local address a datagram was
            # delivered to.  The search arrives as a broadcast, and on a device
            # with both Ethernet and Wi-Fi connected the reply would otherwise
            # leave through whichever interface the routing table prefers -
            # possibly not the one the app is on.  See _send().
            self._pktinfo = False
            if IP_PKTINFO is not None:
                try:
                    self._sock.setsockopt(socket.IPPROTO_IP, IP_PKTINFO, 1)
                    self._pktinfo = True
                except OSError as exc:
                    log.info("IP_PKTINFO unavailable, replies follow the routing table: %s", exc)
            self._sock.bind((self.bind, self.port))
            self._sock.settimeout(0.5)
        except OSError as exc:
            self.last_error = str(exc)
            log.warning("ENPC responder cannot bind %s:%s: %s", self.bind, self.port, exc)
            return

        log.info("ENPC discovery responder listening on %s:%s", self.bind, self.port)
        while not self._stop_event.is_set():
            try:
                data, peer, local = self._receive()
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop_event.is_set():
                    log.debug("ENPC receive failed: %s", exc)
                continue
            if data is None:
                continue
            self._handle_datagram(data, peer, local)

        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    # ------------------------------------------------------------------

    def _receive(self) -> Tuple[Optional[bytes], tuple, Dict[str, Any]]:
        """One datagram, plus which local address and interface received it."""
        assert self._sock is not None
        if not self._pktinfo:
            data, peer = self._sock.recvfrom(4096)
            return data, peer, {}

        data, ancillary, _flags, peer = self._sock.recvmsg(4096, socket.CMSG_SPACE(64))
        local: Dict[str, Any] = {}
        for level, kind, payload in ancillary:
            if level != socket.IPPROTO_IP or kind != IP_PKTINFO:
                continue
            # struct in_pktinfo { int ipi_ifindex; struct in_addr ipi_spec_dst;
            #                     struct in_addr ipi_addr; }
            if len(payload) >= 12:
                index, spec_dst, destination = struct.unpack("I4s4s", payload[:12])
                local = {
                    "ifindex": index,
                    "address": socket.inet_ntoa(spec_dst),
                    "sent_to": socket.inet_ntoa(destination),
                }
        return data, peer, local

    def _handle_datagram(
        self, data: bytes, peer: tuple, local: Optional[Dict[str, Any]] = None
    ) -> None:
        frame = parse_frame(data)
        local = local or {}
        peer_text = f"{peer[0]}:{peer[1]}"
        self.last_peer = peer_text
        self.last_local = str(local.get("address") or "")
        recognised = frame is not None and is_request(frame["magic"])

        entry: Dict[str, Any] = {
            "time": time.time(),
            "protocol": "enpc",
            "peer": peer_text,
            "bytes": len(data),
            "hexdump": hexdump(data),
            "recognised": recognised,
            "magic": frame["magic"].decode("ascii", "replace") if frame else "",
            "function": f"0x{frame['function']:04x}" if frame else "",
            "device_type": frame["device_type"] if frame else None,
            "answered": False,
            "reply_hexdump": "",
            "summary": "",
            "local": str(local.get("address") or ""),
            "sent_to": str(local.get("sent_to") or ""),
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
        # The cycle counter is per source address, so one app walking through
        # its retries gets candidate 1, 2, 3 ... in order.
        replies, candidate = self._build_replies(frame, peer[0])
        entry["candidate"] = candidate
        entry["summary"] = f"{describe_frame(frame)} -> Antwort '{candidate}'"
        entry["reply_hexdump"] = "\n\n".join(hexdump(reply) for reply in replies)

        sent_to: List[str] = []
        for reply in replies:
            sent_to.extend(self._send(reply, peer, local))
        entry["answered"] = bool(sent_to)
        entry["reply_targets"] = sent_to
        self._remember(entry, data)

        if sent_to:
            with self._lock:
                self.replies += 1
            log.info(
                "ENPC: answered %s from %s -> %s (%s)",
                describe_frame(frame),
                peer_text,
                candidate,
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

    def _send(
        self, reply: bytes, peer: tuple, local: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Answer the source port *and* port 3289, from the right interface.

        Some clients broadcast from an ephemeral port but listen for the answer
        on 3289 instead.  Sending to both costs one extra datagram and removes a
        whole class of "no devices found" failures.  The second datagram is
        skipped when the peer is this machine, otherwise we would answer our
        own socket and clutter the probe log.

        The interface matters as much as the port.  The search arrives as a
        broadcast; on a device with Ethernet *and* Wi-Fi up on the same network
        the reply would otherwise leave through whichever interface the routing
        table happens to prefer, with a source address the app never sent
        anything to.  When the kernel told us which local address received the
        request (IP_PKTINFO), the reply is pinned to exactly that one.
        """
        targets = []
        candidates = [(peer[0], peer[1])]
        if peer[1] != self.port and peer[0] not in self._local_addresses():
            candidates.append((peer[0], self.port))

        ancillary = []
        if local and local.get("address"):
            try:
                packed = struct.pack(
                    "I4s4s",
                    int(local.get("ifindex") or 0),
                    socket.inet_aton(local["address"]),
                    b"\x00\x00\x00\x00",
                )
                ancillary = [(socket.IPPROTO_IP, IP_PKTINFO, packed)]
            except (OSError, struct.error) as exc:
                log.debug("cannot pin the reply to %s: %s", local, exc)

        for address in candidates:
            try:
                assert self._sock is not None
                if ancillary:
                    self._sock.sendmsg([reply], ancillary, 0, address)
                else:
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

    def _next_candidate(self, peer_key: str) -> Dict[str, Any]:
        """Which layout to use for this probe.

        In ``cycle`` mode the counter is kept **per peer**, so one app working
        through its retries walks the list from the top rather than sharing a
        global position with anything else on the network.
        """
        if self.reply_style in CANDIDATE_IDS:
            return next(c for c in REPLY_CANDIDATES if c["id"] == self.reply_style)
        with self._lock:
            index = self._cycle.get(peer_key, 0)
            self._cycle[peer_key] = index + 1
        return REPLY_CANDIDATES[index % len(REPLY_CANDIDATES)]

    def _build_replies(self, frame: Dict[str, Any], peer_key: str) -> Tuple[List[bytes], str]:
        """Datagrams to send, plus the name of the layout that produced them.

        Only **one** query is uncertain: the printer's basic information, whose
        payload carries the model name behind five undocumented bytes.  Every
        other query has exactly one answer that a real device is known to give,
        so trying variants there would be pure vandalism - the network status
        query wants MAC and IP, and "who is holding" wants four zero bytes, not
        a model name.  The candidate cycling therefore applies to the name
        query alone.
        """
        magic = reply_magic(frame["magic"]) or MAGIC_QUERY_REPLY
        identity = self._identity()

        uncertain = (
            frame["device_type"] == DEVICE_TYPE_PRINTER
            and frame["function"] == FUNC_BASIC_INFO
        )
        if not uncertain:
            interface = _generated_interface_name(identity["mac"])
            return emulator_reply(frame, magic, identity, interface), "emulator (fest)"

        if self.reply_style == "all":
            datagrams: List[bytes] = []
            for candidate in REPLY_CANDIDATES:
                datagrams.extend(candidate["builder"](frame, magic, identity))
            return datagrams, "all"

        candidate = self._next_candidate(peer_key)
        self.last_candidate = candidate["id"]
        return candidate["builder"](frame, magic, identity), candidate["id"]

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
                candidate=entry.get("candidate", ""),
                local=entry.get("local", ""),
                sent_to=entry.get("sent_to", ""),
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
                "reply_style": self.reply_style,
                "last_candidate": self.last_candidate,
                "last_local": self.last_local,
                "pinned_replies": self._pktinfo,
                "candidates": [
                    {"id": c["id"], "note_de": c["de"], "note_en": c["en"]}
                    for c in REPLY_CANDIDATES
                ],
                "note_de": (
                    "Epson veroeffentlicht das Antwortformat nicht. Im Modus 'cycle' "
                    "wird jede Wiederholung der App mit der naechsten Kandidatenform "
                    "beantwortet - eine Suche probiert damit alle durch. Taucht der "
                    "Drucker auf, steht im Protokoll, welche Form zuletzt gesendet "
                    "wurde; diese laesst sich dann fest einstellen."
                ),
                "note_en": (
                    "Epson does not publish the reply format. In 'cycle' mode each "
                    "retry of the app is answered with the next candidate layout, so "
                    "one search tries them all. When the printer appears, the log "
                    "shows which layout was sent last - that one can then be pinned."
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
