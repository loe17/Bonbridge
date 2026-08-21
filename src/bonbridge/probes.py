"""One shared log for every discovery protocol BonBridge listens on.

The point of this module is measurement, not decoration.  Epson does not
publish how its apps look for printers, and there are at least four candidate
mechanisms on the wire (ENPC on UDP 3289, SNMP on UDP 161, mDNS/DNS-SD, and
plain port probes on 515/631/8008).  Guessing which one a given POS app uses
is a waste of everybody's time.

So BonBridge listens on all of them and writes every single inbound packet
into this one log, with the protocol, the sender and a hexdump.  After one
press of "search for printers" in the app, the log answers the question
outright: *which protocol did the app actually speak, and what exactly did it
send?*  From there the reply can be made to match instead of being invented.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

#: How many probes to keep.  Enough for several search runs, small enough that
#: it never matters on a 256 MB board.
DEFAULT_SIZE = 80


def hexdump(data: bytes, width: int = 16, max_bytes: int = 512) -> str:
    """Classic offset / hex / ASCII dump, shown in the diagnostics view."""
    lines: List[str] = []
    shown = data[:max_bytes]
    for offset in range(0, len(shown), width):
        chunk = shown[offset : offset + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(width * 3 - 1)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:04x}  {hex_part}  |{text}|")
    if len(data) > max_bytes:
        lines.append(f"... {len(data) - max_bytes} further bytes not shown")
    return "\n".join(lines)


class ProbeLog:
    """Thread-safe ring buffer of everything that arrived on a listen port."""

    def __init__(self, size: int = DEFAULT_SIZE):
        self.size = size
        self._lock = threading.Lock()
        self._entries: List[Dict[str, Any]] = []
        self._counts: Dict[str, Dict[str, int]] = {}
        self.enabled = True

    # -- writing -----------------------------------------------------------

    def add(
        self,
        protocol: str,
        peer: str,
        data: bytes,
        *,
        answered: bool = False,
        reply: Optional[bytes] = None,
        summary: str = "",
        note: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        entry = {
            "time": time.time(),
            "protocol": protocol,
            "peer": peer,
            "bytes": len(data),
            "hexdump": hexdump(data),
            "answered": bool(answered),
            "reply_bytes": len(reply) if reply else 0,
            "reply_hexdump": hexdump(reply) if reply else "",
            "summary": summary,
            "note": note,
        }
        # Protocol-specific detail (e.g. which ENPC reply layout was used).
        entry.update(extra)
        with self._lock:
            counter = self._counts.setdefault(protocol, {"requests": 0, "replies": 0})
            counter["requests"] += 1
            if answered:
                counter["replies"] += 1
            if self.enabled:
                self._entries.insert(0, entry)
                del self._entries[self.size :]
        return entry

    # -- reading -----------------------------------------------------------

    def entries(self, limit: int = 0, protocol: str = "") -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._entries)
        if protocol:
            items = [item for item in items if item["protocol"] == protocol]
        return items[:limit] if limit else items

    def counts(self) -> Dict[str, Dict[str, int]]:
        with self._lock:
            return {name: dict(values) for name, values in self._counts.items()}

    def total_requests(self) -> int:
        return sum(values["requests"] for values in self.counts().values())

    def clear(self) -> int:
        with self._lock:
            removed = len(self._entries)
            self._entries = []
            self._counts = {}
            return removed

    def summary(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "protocols": counts,
            "total_requests": sum(v["requests"] for v in counts.values()),
            "total_replies": sum(v["replies"] for v in counts.values()),
            "entries": self.entries(),
        }
