"""Watch the device's own network connection and print a slip when it breaks.

Why this exists: a BonBridge device usually stands next to the printer with no
screen and no keyboard.  When the LAN cable is pulled, the switch loses power
or the Wi-Fi drops, the POS application simply stops printing - and the most
common reaction is "the printer is broken".  The printer is not broken, and it
is still perfectly able to say so on paper, because the USB link to it is
unaffected by a network outage.

So this module answers one question every ``interval`` seconds - *does this
device currently have a usable network connection?* - and reports the
transitions.  What is printed, and on which printer, is decided by the daemon.

How "online" is decided
-----------------------

1. Every non-loopback interface is read from ``/sys/class/net``: ``operstate``
   ("up" / "down" / "unknown") and ``carrier`` (1 = cable plugged in and link
   established).  This is the kernel's own view and needs no helper process,
   which matters on a Raspberry Pi 1.
2. An interface counts as usable when it carries a link **and** has a global
   IP address.  A cable in a dead switch gives carrier but no lease, and a
   Wi-Fi interface that is up without an address is equally useless.
3. Optionally (``gateway_check``) the default gateway is pinged once.  That is
   the only way to notice "associated, addressed, but the router is dead", but
   it costs a subprocess per check, so it is off by default.

References
----------
* ``operstate`` / ``carrier`` semantics:
  https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-net
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import sysinfo

log = logging.getLogger(__name__)

SYS_CLASS_NET = Path("/sys/class/net")

#: Reason keys, translated by the web interface and the printed slip.
REASON_ONLINE = "online"
REASON_NO_INTERFACE = "no_interface"
REASON_NO_CARRIER = "no_carrier"
REASON_NO_ADDRESS = "no_address"
REASON_NO_GATEWAY = "no_gateway"

REASON_TEXT = {
    REASON_ONLINE: ("Netzwerkverbindung in Ordnung", "Network connection is fine"),
    REASON_NO_INTERFACE: (
        "Keine Netzwerkschnittstelle gefunden",
        "No network interface found",
    ),
    REASON_NO_CARRIER: (
        "Kein Signal auf der Leitung - LAN-Kabel oder WLAN-Verbindung unterbrochen",
        "No link - LAN cable unplugged or Wi-Fi disconnected",
    ),
    REASON_NO_ADDRESS: (
        "Verbunden, aber keine IP-Adresse - DHCP/Router antwortet nicht",
        "Link is up but there is no IP address - DHCP/router is not answering",
    ),
    REASON_NO_GATEWAY: (
        "IP-Adresse vorhanden, aber das Gateway antwortet nicht",
        "There is an IP address but the gateway does not answer",
    ),
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def interfaces() -> List[Dict[str, Any]]:
    """Link state of every non-loopback interface, straight from sysfs."""
    result: List[Dict[str, Any]] = []
    try:
        names = sorted(entry.name for entry in SYS_CLASS_NET.iterdir())
    except OSError:
        return result
    for name in names:
        if name == "lo" or name.startswith(("veth", "docker", "br-")):
            continue
        base = SYS_CLASS_NET / name
        operstate = _read(base / "operstate") or "unknown"
        carrier_raw = _read(base / "carrier")
        # `carrier` returns EINVAL while the interface is administratively down,
        # which surfaces as an empty string - treat that as "no link".
        carrier = carrier_raw == "1"
        result.append(
            {
                "name": name,
                "operstate": operstate,
                "carrier": carrier,
                "wireless": (base / "wireless").exists() or name.startswith("wl"),
                "mac": _read(base / "address"),
                "addresses": [],
            }
        )
    return result


def default_gateway() -> str:
    """Default IPv4 gateway from ``/proc/net/route`` - no subprocess needed."""
    try:
        with open("/proc/net/route", "r", encoding="utf-8") as handle:
            next(handle, None)  # header
            for line in handle:
                fields = line.split()
                if len(fields) > 2 and fields[1] == "00000000":
                    raw = int(fields[2], 16)
                    return ".".join(str((raw >> shift) & 0xFF) for shift in (0, 8, 16, 24))
    except (OSError, ValueError, StopIteration):
        pass
    return ""


def ping(host: str, timeout: float = 2.0) -> bool:
    if not host or not shutil.which("ping"):
        return True  # cannot tell - do not raise a false alarm
    try:
        result = subprocess.run(  # noqa: S603 - fixed command
            ["ping", "-n", "-c", "1", "-W", str(max(1, int(timeout))), host],
            capture_output=True,
            timeout=timeout + 3,
            check=False,
        )
        return result.returncode == 0
    except Exception as exc:  # noqa: BLE001
        log.debug("ping %s failed: %s", host, exc)
        return True


def snapshot(gateway_check: bool = False) -> Dict[str, Any]:
    """Current network state with the reason it is considered up or down."""
    links = interfaces()
    addresses = sysinfo.ip_addresses(ttl=0)
    by_interface: Dict[str, List[str]] = {}
    for entry in addresses:
        by_interface.setdefault(entry["interface"], []).append(entry["address"])
    for link in links:
        link["addresses"] = by_interface.get(link["name"], [])

    gateway = default_gateway()
    usable = [
        link
        for link in links
        if link["carrier"] and link["operstate"] in ("up", "unknown") and link["addresses"]
    ]

    if not links:
        reason = REASON_NO_INTERFACE
    elif not any(link["carrier"] for link in links):
        reason = REASON_NO_CARRIER
    elif not usable:
        reason = REASON_NO_ADDRESS
    elif gateway_check and gateway and not ping(gateway):
        reason = REASON_NO_GATEWAY
    else:
        reason = REASON_ONLINE

    return {
        "online": reason == REASON_ONLINE,
        "reason": reason,
        "reason_de": REASON_TEXT[reason][0],
        "reason_en": REASON_TEXT[reason][1],
        "interfaces": links,
        "gateway": gateway,
        "ip": sysinfo.primary_ipv4() if reason == REASON_ONLINE else "",
        "checked_at": time.time(),
    }


class NetworkWatcher(threading.Thread):
    """Polls :func:`snapshot` and reports state *changes* to a callback.

    The callback receives ``(online, snapshot, offline_since)`` and is only
    invoked on a transition - never once per check - so nothing is printed
    repeatedly while the network stays down.

    ``confirmations`` guards against flapping: a single missed check (a Wi-Fi
    roam, a switch renegotiating) does not count as an outage; the state has to
    hold for that many consecutive checks before it is reported.
    """

    def __init__(
        self,
        on_change: Callable[[bool, Dict[str, Any], Optional[float]], None],
        *,
        interval: float = 60.0,
        gateway_check: bool = False,
        confirmations: int = 2,
    ):
        super().__init__(name="netwatch", daemon=True)
        self.on_change = on_change
        self.interval = max(10.0, float(interval))
        self.gateway_check = bool(gateway_check)
        self.confirmations = max(1, int(confirmations))
        self._stop_event = threading.Event()

        self.online: Optional[bool] = None
        self.last: Dict[str, Any] = {}
        self.offline_since: Optional[float] = None
        self.changes = 0
        self._pending: Optional[bool] = None
        self._pending_count = 0

    # -- polling -----------------------------------------------------------

    def check_once(self, announce: bool = True) -> Dict[str, Any]:
        """Run one check.  Returns the snapshot; may fire the callback."""
        try:
            current = snapshot(self.gateway_check)
        except Exception as exc:  # noqa: BLE001 - a watchdog must not crash
            log.warning("network check failed: %s", exc)
            return self.last
        self.last = current
        online = bool(current["online"])

        if self.online is None:
            # First check after start: this *is* the initial state, report it
            # straight away when the device starts up without a network.
            self.online = online
            if not online:
                self.offline_since = time.time()
                self.changes += 1
                if announce:
                    self._fire(False, current, self.offline_since)
            return current

        if online == self.online:
            self._pending = None
            self._pending_count = 0
            return current

        # State differs - require it to hold for `confirmations` checks.
        if self._pending is online:
            self._pending_count += 1
        else:
            self._pending = online
            self._pending_count = 1
        if self._pending_count < self.confirmations:
            log.debug(
                "network state change to online=%s pending (%s/%s)",
                online,
                self._pending_count,
                self.confirmations,
            )
            return current

        self._pending = None
        self._pending_count = 0
        was_offline_since = self.offline_since
        self.online = online
        self.changes += 1
        self.offline_since = None if online else time.time()
        if announce:
            self._fire(online, current, was_offline_since)
        return current

    def _fire(self, online: bool, current: Dict[str, Any], offline_since: Optional[float]) -> None:
        log.warning(
            "network %s (%s)", "restored" if online else "lost", current.get("reason")
        )
        try:
            self.on_change(online, current, offline_since)
        except Exception as exc:  # noqa: BLE001
            log.warning("network change handler failed: %s", exc)

    def run(self) -> None:
        # The very first check happens immediately so a device that boots
        # without a network says so within seconds, not after one interval.
        self.check_once()
        while not self._stop_event.wait(self.interval):
            self.check_once()

    def stop(self) -> None:
        self._stop_event.set()

    # -- reporting ---------------------------------------------------------

    def snapshot_dict(self) -> Dict[str, Any]:
        data = dict(self.last or {})
        data.update(
            {
                "enabled": True,
                "interval": self.interval,
                "gateway_check": self.gateway_check,
                "confirmations": self.confirmations,
                "changes": self.changes,
                "offline_since": self.offline_since,
            }
        )
        return data


def describe_links(state: Dict[str, Any], german: bool = True) -> List[Tuple[str, str]]:
    """Interface list formatted for the printed slip."""
    rows: List[Tuple[str, str]] = []
    for link in state.get("interfaces") or []:
        if link.get("addresses"):
            value = ", ".join(link["addresses"])
        elif link.get("carrier"):
            value = "verbunden, keine IP" if german else "link up, no IP"
        else:
            value = "kein Signal" if german else "no link"
        rows.append((link.get("name", "?"), value))
    return rows
