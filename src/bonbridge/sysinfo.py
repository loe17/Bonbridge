"""System information for the diagnostics page and the support report.

The overview endpoint is polled every few seconds by every open browser tab.
Anything in here that forks a helper process (``ip``, ``vcgencmd``) or reads
sysfs is therefore wrapped in a short time-to-live cache: on a single-core
700 MHz board (Raspberry Pi 1 / Zero) a fork+exec every five seconds is a
measurable share of the CPU, and none of these values change that quickly.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import __version__

_cache_lock = threading.Lock()
_cache: Dict[str, Tuple[float, Any]] = {}


def cached(key: str, ttl: float, producer: Callable[[], Any]) -> Any:
    """Return ``producer()``, reusing the previous result for ``ttl`` seconds.

    ``ttl <= 0`` disables caching, which keeps the tests honest.
    """
    if ttl <= 0:
        return producer()
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(key)
        if entry is not None and now - entry[0] < ttl:
            return entry[1]
    value = producer()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    """Drop all cached readings (used by tests and after config changes)."""
    with _cache_lock:
        _cache.clear()


def _run(command: List[str], timeout: float = 5.0) -> str:
    """Run a helper command, returning its output or an explanatory string."""
    if not shutil.which(command[0]):
        return f"({command[0]} not installed)"
    try:
        result = subprocess.run(  # noqa: S603 - fixed command list, no shell
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return f"({command[0]} failed: {exc})"
    output = (result.stdout or "") + (result.stderr or "")
    return output.strip() or "(no output)"


def hostname() -> str:
    return socket.gethostname()


def ip_addresses(ttl: float = 15.0) -> List[Dict[str, str]]:
    """All global IPv4/IPv6 addresses with their interface names.

    Cached for ``ttl`` seconds because it shells out to ``ip``.
    """
    return cached("ip_addresses", ttl, _read_ip_addresses)


def _read_ip_addresses() -> List[Dict[str, str]]:
    addresses: List[Dict[str, str]] = []
    output = _run(["ip", "-o", "addr", "show", "scope", "global"])
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] in ("inet", "inet6"):
            addresses.append(
                {
                    "interface": parts[1],
                    "family": "ipv4" if parts[2] == "inet" else "ipv6",
                    "address": parts[3].split("/")[0],
                    "cidr": parts[3],
                }
            )
    if not addresses:  # fallback without iproute2
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                address = info[4][0]
                if address.startswith("127.") or address == "::1":
                    continue
                addresses.append(
                    {
                        "interface": "?",
                        "family": "ipv4" if ":" not in address else "ipv6",
                        "address": address,
                        "cidr": address,
                    }
                )
        except OSError:
            pass
    # de-duplicate, keep order
    seen = set()
    unique = []
    for entry in addresses:
        key = (entry["interface"], entry["address"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def primary_ipv4() -> str:
    """Best guess at the address a phone on the same LAN should use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.settimeout(0.5)
            probe.connect(("192.0.2.1", 9))  # TEST-NET-1, no traffic is sent
            return probe.getsockname()[0]
    except OSError:
        pass
    for entry in ip_addresses():
        if entry["family"] == "ipv4":
            return entry["address"]
    return "127.0.0.1"


def os_release() -> Dict[str, str]:
    """Contents of ``/etc/os-release``; cached, it only changes on upgrade."""
    return cached("os_release", 300.0, _read_os_release)


def _read_os_release() -> Dict[str, str]:
    info: Dict[str, str] = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for line in handle:
                if "=" in line:
                    key, _, value = line.strip().partition("=")
                    info[key] = value.strip('"')
    except OSError:
        pass
    return info


def model_name() -> str:
    """Raspberry Pi / board model, or the DMI product name on x86."""
    return cached("model_name", 3600.0, _read_model_name)


def _read_model_name() -> str:
    for path in ("/proc/device-tree/model", "/sys/devices/virtual/dmi/id/product_name"):
        try:
            with open(path, "rb") as handle:
                value = handle.read().decode("utf-8", "replace").strip("\x00 \n")
                if value:
                    return value
        except OSError:
            continue
    return platform.machine()


def cpu_temperature() -> Optional[float]:
    for path in (
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
    ):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = float(handle.read().strip())
                return raw / 1000.0 if raw > 1000 else raw
        except (OSError, ValueError):
            continue
    return None


def uptime_seconds() -> Optional[float]:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as handle:
            return float(handle.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def memory() -> Dict[str, int]:
    result: Dict[str, int] = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                match = re.match(r"^(\w+):\s+(\d+) kB", line)
                if match and match.group(1) in ("MemTotal", "MemAvailable"):
                    result[match.group(1)] = int(match.group(2)) * 1024
    except OSError:
        pass
    return result


def disk() -> Dict[str, int]:
    try:
        usage = shutil.disk_usage("/")
        return {"total": usage.total, "used": usage.used, "free": usage.free}
    except OSError:
        return {}


def load_average() -> List[float]:
    try:
        return list(os.getloadavg())
    except (OSError, AttributeError):
        return []


def summary() -> Dict[str, Any]:
    release = os_release()
    return {
        "bonbridge_version": __version__,
        "hostname": hostname(),
        "primary_ip": primary_ipv4(),
        "addresses": ip_addresses(),
        "model": model_name(),
        "architecture": platform.machine(),
        "kernel": platform.release(),
        "os": release.get("PRETTY_NAME") or release.get("NAME") or platform.system(),
        "python": platform.python_version(),
        "uptime": uptime_seconds(),
        "cpu_temperature": cpu_temperature(),
        "memory": memory(),
        "disk": disk(),
        "load": load_average(),
        "time": time.time(),
        "timezone": time.strftime("%Z%z"),
    }


def diagnostics() -> Dict[str, str]:
    """Raw command output used by the diagnostics page and support report."""
    return {
        "lsusb": _run(["lsusb"]),
        "usb_devices": _run(["ls", "-l", "/dev/usb/"]),
        "tty_devices": _run(["bash", "-lc", "ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null"]),
        "listening_ports": _run(["ss", "-tlnp"]),
        "ip_addresses": _run(["ip", "-o", "addr"]),
        "routes": _run(["ip", "route"]),
        "dmesg_tail": _run(["bash", "-lc", "dmesg 2>/dev/null | tail -n 40"]),
        "service_status": _run(["systemctl", "--no-pager", "status", "bonbridge"], timeout=8.0),
        "cups_status": _run(["systemctl", "--no-pager", "is-active", "cups"], timeout=8.0),
        "kernel_modules": _run(["bash", "-lc", "lsmod | grep -E 'usblp|cdc_acm|ftdi|ch34' || true"]),
    }
