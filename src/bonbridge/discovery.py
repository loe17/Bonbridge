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
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

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


def build_frame(
    magic: bytes, function: bytes, payload: bytes = b"", little_endian: bool = False
) -> bytes:
    """``<magic:6><function:4><len(payload):4><payload>``.

    The length is **big endian**.  That is not a guess: in the captured reply of
    a real TM-m30 the field reads ``00 00 00 17`` and the payload that follows
    is exactly 23 bytes, while a little-endian reading would be 385'875'968.
    """
    length = struct.pack("<I" if little_endian else ">I", len(payload))
    return magic + function[:4].ljust(4, b"\x00") + length + payload


def build_echo_frame(magic: bytes, header_tail: bytes, payload: bytes = b"") -> bytes:
    """Mirror the request header verbatim and append a payload.

    Kept only so the old behaviour can still be selected for comparison.  It is
    structurally broken against a real client: the request declares a payload
    length of zero, so a parser that trusts the length field never looks at the
    payload at all.
    """
    return magic + header_tail[:8].ljust(8, b"\x00") + payload


#: Payload of the captured TM-m30 discovery reply, minus the model name.
#: The meaning of these five bytes is unknown; they are reproduced verbatim
#: because a real device sent them and the client evidently accepts them.
DEVICE_PREFIX = b"\x00\x05\x01\x02\x01"

#: Total payload size of that reply.  The name is NUL-padded up to it.
DEVICE_PAYLOAD_LEN = 0x85  # 133

#: Trailing bytes of the captured network-info reply, meaning unknown.
NETWORK_TAIL = b"\x80\x7c"

#: Function id of the network-info reply the device sent unprompted.
FUNC_NETWORK_REPLY = b"\x00\x00\x00\x10"


def device_payload(model: bytes) -> bytes:
    """The captured discovery payload with our model name substituted."""
    body = DEVICE_PREFIX + model[: DEVICE_PAYLOAD_LEN - len(DEVICE_PREFIX) - 1]
    return body.ljust(DEVICE_PAYLOAD_LEN, b"\x00")


def network_payload(identity: Dict[str, bytes]) -> bytes:
    """The captured network-info payload with our own addresses."""
    return (
        identity["mac"]
        + b"\x00\x00\x04"
        + identity["ip"]
        + identity["netmask"]
        + identity["gateway"]
        + NETWORK_TAIL
    )


#: Candidate reply layouts, most-likely first.
#:
#: Each entry is ``(id, description_de, description_en, builder)`` where the
#: builder returns the list of datagrams to send.  They exist because the
#: payload format is not published: instead of presenting one interpretation as
#: fact, BonBridge can try them in turn and record which one it used.
def _c_device(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return [build_frame(magic, frame["function_bytes"], device_payload(identity["model"]))]


def _c_device_net(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return [
        build_frame(magic, frame["function_bytes"], device_payload(identity["model"])),
        build_frame(magic, FUNC_NETWORK_REPLY, network_payload(identity)),
    ]


def _c_device_le(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return [
        build_frame(
            magic, frame["function_bytes"], device_payload(identity["model"]), little_endian=True
        )
    ]


def _c_name_padded(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    payload = identity["model"][: DEVICE_PAYLOAD_LEN - 1].ljust(DEVICE_PAYLOAD_LEN, b"\x00")
    return [build_frame(magic, frame["function_bytes"], payload)]


def _c_name_plain(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    return [build_frame(magic, frame["function_bytes"], identity["model"] + b"\x00")]


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
    return [build_frame(magic, frame["function_bytes"], payload)]


def _c_legacy_echo(frame: Dict[str, Any], magic: bytes, identity: Dict[str, bytes]) -> List[bytes]:
    payload = identity["name"] + b"\x00" + identity["model"] + b"\x00" + identity["mac"] + identity["ip"]
    return [build_echo_frame(magic, frame["header_tail"], payload)]


REPLY_CANDIDATES: List[Dict[str, Any]] = [
    {
        "id": "device",
        "de": "Antwort eines echten TM-m30, Modellname ersetzt (133 Byte, Big Endian)",
        "en": "Reply of a real TM-m30 with the model name swapped (133 bytes, big endian)",
        "builder": _c_device,
    },
    {
        "id": "device+net",
        "de": "Wie 'device', zusätzlich die Netzwerk-Info-Antwort (MAC, IP, Maske, Gateway)",
        "en": "Like 'device' plus the network-info reply (MAC, IP, netmask, gateway)",
        "builder": _c_device_net,
    },
    {
        "id": "device-le",
        "de": "Wie 'device', aber Längenfeld Little Endian - falls der Client anders liest",
        "en": "Like 'device' but with a little-endian length field, in case the client differs",
        "builder": _c_device_le,
    },
    {
        "id": "name-padded",
        "de": "Nur der Modellname, auf 133 Byte mit Nullen aufgefüllt",
        "en": "Just the model name, NUL-padded to 133 bytes",
        "builder": _c_name_padded,
    },
    {
        "id": "name-plain",
        "de": "Nur der Modellname mit abschließender Null, keine Auffüllung",
        "en": "Just the model name with a terminating NUL, no padding",
        "builder": _c_name_plain,
    },
    {
        "id": "identity",
        "de": "MAC, IP, Maske, Gateway, Modell, Gerätename - alles am Stück",
        "en": "MAC, IP, netmask, gateway, model, device name - all in one block",
        "builder": _c_identity,
    },
    {
        "id": "legacy-echo",
        "de": "Alte Fassung: Anfrage-Kopf gespiegelt (Längenfeld bleibt 0 - nachweislich falsch)",
        "en": "Old behaviour: request header mirrored (length stays 0 - demonstrably wrong)",
        "builder": _c_legacy_echo,
    },
]

CANDIDATE_IDS = [entry["id"] for entry in REPLY_CANDIDATES]

#: ``cycle`` walks the list, one candidate per probe.  Any candidate id pins
#: that one layout.  ``all`` sends every candidate at once - noisy, but useful
#: as a last resort when a client only ever sends a single probe.
REPLY_STYLES = ("cycle", "all", *CANDIDATE_IDS)


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
        "declared_length": struct.unpack(">I", header_tail[4:8])[0],
        "declared_length_le": struct.unpack("<I", header_tail[4:8])[0],
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
        self.reply_style = reply_style if reply_style in REPLY_STYLES else "cycle"
        #: Shared log across all discovery protocols (bonbridge.probes.ProbeLog).
        self.probe_log = probe_log

        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._local_cache: Optional[set] = None
        #: Position in REPLY_CANDIDATES per peer, for ``cycle`` mode.
        self._cycle: Dict[str, int] = {}
        self.last_candidate = ""

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
        # The cycle counter is per source address, so one app walking through
        # its retries gets candidate 1, 2, 3 ... in order.
        replies, candidate = self._build_replies(frame, peer[0])
        entry["candidate"] = candidate
        entry["summary"] = (
            f"{entry['magic']} function {entry['function']} -> Antwort '{candidate}'"
        )
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
        """Datagrams to send, plus the name of the layout that produced them."""
        magic = reply_magic(frame["magic"]) or MAGIC_QUERY_REPLY
        identity = self._identity()

        # "Who is holding this printer?" has a known answer and no room for
        # variants: all zeroes means "nobody, it is free".
        if frame["function"] == FUNC_WHO_IS_HOLDING:
            return [build_frame(magic, frame["function_bytes"], b"\x00" * 4)], "who-is-holding"

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
