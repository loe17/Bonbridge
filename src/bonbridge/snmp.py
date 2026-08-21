"""A minimal SNMP v1 agent so BonBridge answers like a network printer.

Why this is here
----------------
Epson's own Ethernet interface for the TM series (UB-E04) speaks **SNMP v1 on
UDP 161 with the read community "public"** - it is listed in the interface's
technical reference right next to LPR, port 9100 and ENPC.  Printer discovery
tools and POS apps make heavy use of that: sweeping a subnet with one SNMP
``GetRequest`` for ``sysDescr`` is by far the cheapest way to find every
printer on it, and unlike ENPC the protocol is public and unambiguous.

BonBridge previously answered ENPC and mDNS but was completely silent on 161,
so any app that searched this way found nothing - correctly, because there was
nothing to find.

This implements just enough SNMP to be discovered: ``GetRequest`` and
``GetNextRequest`` for the handful of objects a printer is expected to expose.
No ``SetRequest`` (nothing here should be settable from the LAN), no traps, no
v3.  BER encoding and decoding are done by hand - a print bridge should not
need pysnmp for 200 lines of tag/length/value.

References
----------
* Epson UB-E04 Technical Reference Guide - protocol list incl. SNMP v1/161
  https://files.support.epson.com/pdf/ube04_/ube04_trg.pdf
* RFC 1157 (SNMP v1), RFC 1213 (MIB-II), RFC 3805 (Printer MIB)
* Full reference list: docs/en/09-references.md
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .probes import ProbeLog

log = logging.getLogger(__name__)

SNMP_PORT = 161

# -- BER tags ---------------------------------------------------------------
TAG_INTEGER = 0x02
TAG_OCTET_STRING = 0x04
TAG_NULL = 0x05
TAG_OID = 0x06
TAG_SEQUENCE = 0x30
TAG_IPADDRESS = 0x40
TAG_COUNTER32 = 0x41
TAG_GAUGE32 = 0x42
TAG_TIMETICKS = 0x43

PDU_GET = 0xA0
PDU_GETNEXT = 0xA1
PDU_RESPONSE = 0xA2
PDU_SET = 0xA3

ERROR_NO_SUCH_NAME = 2
ERROR_READ_ONLY = 4


# --------------------------------------------------------------------------
# BER
# --------------------------------------------------------------------------


def _encode_length(length: int) -> bytes:
    if length < 0x80:
        return bytes((length,))
    raw = b""
    while length:
        raw = bytes((length & 0xFF,)) + raw
        length >>= 8
    return bytes((0x80 | len(raw),)) + raw


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes((tag,)) + _encode_length(len(value)) + value


def encode_integer(value: int, tag: int = TAG_INTEGER) -> bytes:
    raw = b""
    remaining = int(value)
    if remaining == 0:
        raw = b"\x00"
    else:
        while remaining not in (0, -1):
            raw = bytes((remaining & 0xFF,)) + raw
            remaining >>= 8
        if value > 0 and raw[0] & 0x80:
            raw = b"\x00" + raw
        elif value < 0 and not raw[0] & 0x80:
            raw = b"\xff" + raw
    return _tlv(tag, raw)


def encode_oid(oid: str) -> bytes:
    parts = [int(part) for part in oid.strip(".").split(".")]
    if len(parts) < 2:
        raise ValueError(f"invalid OID: {oid}")
    raw = bytearray([parts[0] * 40 + parts[1]])
    for part in parts[2:]:
        if part < 0x80:
            raw.append(part)
            continue
        chunk = bytearray()
        chunk.insert(0, part & 0x7F)
        part >>= 7
        while part:
            chunk.insert(0, (part & 0x7F) | 0x80)
            part >>= 7
        raw.extend(chunk)
    return _tlv(TAG_OID, bytes(raw))


def decode_length(data: bytes, offset: int) -> Tuple[int, int]:
    first = data[offset]
    offset += 1
    if first < 0x80:
        return first, offset
    count = first & 0x7F
    value = 0
    for _ in range(count):
        value = (value << 8) | data[offset]
        offset += 1
    return value, offset


def decode_tlv(data: bytes, offset: int = 0) -> Tuple[int, bytes, int]:
    """Returns ``(tag, value, next_offset)``."""
    tag = data[offset]
    length, offset = decode_length(data, offset + 1)
    value = data[offset : offset + length]
    return tag, value, offset + length


def decode_integer(value: bytes) -> int:
    if not value:
        return 0
    result = int.from_bytes(value, "big", signed=bool(value[0] & 0x80))
    return result


def decode_oid(value: bytes) -> str:
    if not value:
        return ""
    parts = [value[0] // 40, value[0] % 40]
    current = 0
    for byte in value[1:]:
        current = (current << 7) | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(current)
            current = 0
    return ".".join(str(part) for part in parts)


def oid_key(oid: str) -> Tuple[int, ...]:
    """Sortable form, so ``GetNext`` walks the tree in the right order."""
    return tuple(int(part) for part in oid.strip(".").split(".") if part != "")


# --------------------------------------------------------------------------
# The object tree
# --------------------------------------------------------------------------

#: Epson's IANA enterprise number.  Discovery tools recognise a printer as an
#: Epson device by ``sysObjectID`` sitting under this arc.
EPSON_ENTERPRISE = "1.3.6.1.4.1.1248"


def build_mib(
    *,
    model: str,
    device_name: str,
    serial: str = "",
    mac: bytes = b"",
    uptime_seconds: float = 0.0,
) -> List[Tuple[str, int, Any]]:
    """The objects a printer is expected to expose, in OID order.

    Values are ``(oid, tag, value)``.  Kept deliberately small: everything here
    is something a discovery tool actually asks for.
    """
    description = f"EPSON {model}" if not model.upper().startswith("EPSON") else model
    ticks = int(max(0.0, uptime_seconds) * 100) % (2**32)
    entries: List[Tuple[str, int, Any]] = [
        # -- MIB-II system group (RFC 1213) --------------------------------
        ("1.3.6.1.2.1.1.1.0", TAG_OCTET_STRING, description),
        ("1.3.6.1.2.1.1.2.0", TAG_OID, EPSON_ENTERPRISE),
        ("1.3.6.1.2.1.1.3.0", TAG_TIMETICKS, ticks),
        ("1.3.6.1.2.1.1.4.0", TAG_OCTET_STRING, ""),
        ("1.3.6.1.2.1.1.5.0", TAG_OCTET_STRING, device_name),
        ("1.3.6.1.2.1.1.6.0", TAG_OCTET_STRING, ""),
        # sysServices: bit 3 (application) - what printers report.
        ("1.3.6.1.2.1.1.7.0", TAG_INTEGER, 72),
        # -- interfaces: the MAC address, which tools use as the device id --
        ("1.3.6.1.2.1.2.1.0", TAG_INTEGER, 1),
        ("1.3.6.1.2.1.2.2.1.1.1", TAG_INTEGER, 1),
        ("1.3.6.1.2.1.2.2.1.2.1", TAG_OCTET_STRING, "Ethernet"),
        ("1.3.6.1.2.1.2.2.1.3.1", TAG_INTEGER, 6),
        ("1.3.6.1.2.1.2.2.1.6.1", TAG_OCTET_STRING, mac),
        # -- host resources: hrDeviceDescr / hrPrinterStatus ----------------
        ("1.3.6.1.2.1.25.3.2.1.1.1", TAG_INTEGER, 1),
        ("1.3.6.1.2.1.25.3.2.1.2.1", TAG_OID, "1.3.6.1.2.1.25.3.1.5"),  # printer
        ("1.3.6.1.2.1.25.3.2.1.3.1", TAG_OCTET_STRING, description),
        ("1.3.6.1.2.1.25.3.2.1.5.1", TAG_INTEGER, 2),  # running
        ("1.3.6.1.2.1.25.3.5.1.1.1", TAG_INTEGER, 3),  # hrPrinterStatus: idle
        ("1.3.6.1.2.1.25.3.5.1.2.1", TAG_OCTET_STRING, b"\x00"),
        # -- printer MIB (RFC 3805) ----------------------------------------
        ("1.3.6.1.2.1.43.5.1.1.1.1", TAG_INTEGER, 1),
        ("1.3.6.1.2.1.43.5.1.1.16.1", TAG_OCTET_STRING, device_name),
        ("1.3.6.1.2.1.43.5.1.1.17.1", TAG_OCTET_STRING, serial),
        # Interpreter description - some tools read the language from here.
        ("1.3.6.1.2.1.43.15.1.1.5.1.1", TAG_OCTET_STRING, "ESC/POS"),
        # -- Epson private arc ---------------------------------------------
        (f"{EPSON_ENTERPRISE}.1.1.3.1.3.8.0", TAG_OCTET_STRING, description),
    ]
    return sorted(entries, key=lambda item: oid_key(item[0]))


def encode_value(tag: int, value: Any) -> bytes:
    if tag == TAG_OCTET_STRING:
        raw = value if isinstance(value, bytes) else str(value).encode("utf-8", "replace")
        return _tlv(TAG_OCTET_STRING, raw)
    if tag == TAG_OID:
        return encode_oid(str(value))
    if tag in (TAG_INTEGER, TAG_COUNTER32, TAG_GAUGE32, TAG_TIMETICKS):
        return encode_integer(int(value), tag)
    if tag == TAG_IPADDRESS:
        return _tlv(TAG_IPADDRESS, socket.inet_aton(str(value)))
    return _tlv(TAG_NULL, b"")


# --------------------------------------------------------------------------
# Request handling
# --------------------------------------------------------------------------


def parse_request(data: bytes) -> Optional[Dict[str, Any]]:
    """Decode an SNMP v1/v2c message.  Returns ``None`` if it is not one."""
    try:
        tag, message, _ = decode_tlv(data)
        if tag != TAG_SEQUENCE:
            return None
        offset = 0
        tag, value, offset = decode_tlv(message, offset)
        version = decode_integer(value)
        tag, value, offset = decode_tlv(message, offset)
        community = bytes(value)
        pdu_tag, pdu, _ = decode_tlv(message, offset)
        if pdu_tag not in (PDU_GET, PDU_GETNEXT, PDU_SET):
            return None

        offset = 0
        tag, value, offset = decode_tlv(pdu, offset)
        request_id = decode_integer(value)
        tag, value, offset = decode_tlv(pdu, offset)  # error-status
        tag, value, offset = decode_tlv(pdu, offset)  # error-index
        tag, bindings, _ = decode_tlv(pdu, offset)

        oids: List[str] = []
        position = 0
        while position < len(bindings):
            tag, binding, position = decode_tlv(bindings, position)
            if tag != TAG_SEQUENCE:
                continue
            inner_tag, oid_value, _ = decode_tlv(binding, 0)
            if inner_tag == TAG_OID:
                oids.append(decode_oid(oid_value))
        return {
            "version": version,
            "community": community,
            "pdu": pdu_tag,
            "request_id": request_id,
            "oids": oids,
        }
    except (IndexError, ValueError) as exc:
        log.debug("not an SNMP message: %s", exc)
        return None


def build_response(
    request: Dict[str, Any],
    mib: List[Tuple[str, int, Any]],
    error_status: int = 0,
    error_index: int = 0,
) -> bytes:
    lookup = {oid: (tag, value) for oid, tag, value in mib}
    ordered = [oid for oid, _, _ in mib]

    bindings = b""
    status = error_status
    index = error_index
    for position, oid in enumerate(request["oids"], start=1):
        if request["pdu"] == PDU_GETNEXT:
            following = [entry for entry in ordered if oid_key(entry) > oid_key(oid)]
            target = following[0] if following else None
        else:
            target = oid if oid in lookup else None

        if target is None:
            # v1 has no "endOfMibView"; the honest answer is noSuchName.
            if not status:
                status, index = ERROR_NO_SUCH_NAME, position
            bindings += _tlv(TAG_SEQUENCE, encode_oid(oid) + _tlv(TAG_NULL, b""))
            continue
        tag, value = lookup[target]
        bindings += _tlv(TAG_SEQUENCE, encode_oid(target) + encode_value(tag, value))

    pdu = (
        encode_integer(request["request_id"])
        + encode_integer(status)
        + encode_integer(index)
        + _tlv(TAG_SEQUENCE, bindings)
    )
    message = (
        encode_integer(request["version"])
        + _tlv(TAG_OCTET_STRING, request["community"])
        + _tlv(PDU_RESPONSE, pdu)
    )
    return _tlv(TAG_SEQUENCE, message)


class SnmpResponder(threading.Thread):
    """Answers SNMP discovery queries on UDP 161."""

    def __init__(
        self,
        info_provider: Callable[[], Dict[str, Any]],
        probe_log: ProbeLog,
        *,
        bind: str = "0.0.0.0",
        port: int = SNMP_PORT,
        community: str = "public",
    ):
        super().__init__(name="snmp-responder", daemon=True)
        self.info_provider = info_provider
        self.probe_log = probe_log
        self.bind = bind
        self.port = port
        self.community = community.encode("ascii", "replace")

        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        self.started_at = time.time()
        self.requests = 0
        self.replies = 0
        self.last_error: Optional[str] = None

    def current_mib(self) -> List[Tuple[str, int, Any]]:
        info = self.info_provider() or {}
        return build_mib(
            model=str(info.get("model") or "TM-T88V"),
            device_name=str(info.get("name") or "BonBridge"),
            serial=str(info.get("serial") or ""),
            mac=info.get("mac") or b"",
            uptime_seconds=time.time() - self.started_at,
        )

    def run(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.bind, self.port))
            self._sock.settimeout(0.5)
        except OSError as exc:
            self.last_error = str(exc)
            log.warning("SNMP responder cannot bind %s:%s: %s", self.bind, self.port, exc)
            return
        log.info("SNMP responder listening on %s:%s", self.bind, self.port)

        while not self._stop_event.is_set():
            try:
                data, peer = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop_event.is_set():
                    log.debug("SNMP receive failed: %s", exc)
                continue
            self._handle_datagram(data, peer)

        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    def _handle_datagram(self, data: bytes, peer: tuple) -> None:
        peer_text = f"{peer[0]}:{peer[1]}"
        self.requests += 1
        request = parse_request(data)
        if request is None:
            self.probe_log.add("snmp", peer_text, data, summary="not an SNMP message")
            return

        names = {PDU_GET: "Get", PDU_GETNEXT: "GetNext", PDU_SET: "Set"}
        summary = f"{names.get(request['pdu'], '?')} {', '.join(request['oids'][:4])}"

        if request["pdu"] == PDU_SET:
            # Nothing here is settable from the network, and a print bridge that
            # can be reconfigured by an unauthenticated UDP packet would be a
            # bad idea.  Answer honestly instead of ignoring the request.
            reply = build_response(request, self.current_mib(), ERROR_READ_ONLY, 1)
        else:
            reply = build_response(request, self.current_mib())

        try:
            assert self._sock is not None
            self._sock.sendto(reply, peer)
            self.replies += 1
            answered = True
        except OSError as exc:
            log.debug("SNMP reply to %s failed: %s", peer_text, exc)
            answered = False

        self.probe_log.add(
            "snmp", peer_text, data, answered=answered, reply=reply, summary=summary
        )
        log.info("SNMP: answered %s from %s", summary, peer_text)

    def stop(self) -> None:
        self._stop_event.set()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "port": self.port,
            "listening": self._sock is not None and self.last_error is None,
            "requests": self.requests,
            "replies": self.replies,
            "error": self.last_error,
            "community": self.community.decode("ascii", "replace"),
        }
