"""Passive listeners whose only job is to record who knocks.

ENPC, SNMP and LPD have real responders.  For everything else a POS app might
try - IPP on 631, Epson's ePOS-Device port 8008, SSDP on 1900 - guessing a
correct answer would be irresponsible, but *noticing the attempt* costs
nothing and is exactly the information that is missing.

So these listeners accept the connection or datagram, read whatever arrives,
write it to the shared probe log with a hexdump, and close.  After one search
run in the POS app the log says which door the app knocked on.  That turns
"the printer is not found" from a guessing game into a measurement.

Nothing here ever answers, on purpose: a half-implemented IPP or ePOS reply
would be worse than silence, because the client would then believe it is
talking to a working device.
"""

from __future__ import annotations

import logging
import socket
import socketserver
import threading
from typing import Any, Dict, List, Optional

from .probes import ProbeLog

log = logging.getLogger(__name__)

#: What each watched port is, so the diagnostics page can say something useful
#: rather than just printing a number.
PORT_NAMES = {
    80: ("HTTP", "Webseite des Druckers / printer web page"),
    161: ("SNMP", "Statusabfrage / status query"),
    515: ("LPD/LPR", "Druckauftrag / print job"),
    631: ("IPP", "Internet Printing Protocol / Internet Printing Protocol"),
    1900: ("SSDP", "UPnP-Suche / UPnP discovery"),
    3289: ("ENPC", "Epson-Druckersuche / Epson printer search"),
    8008: ("ePOS-Device", "Epson ePOS-Device / ePOS-Print"),
    9100: ("RAW", "JetDirect / ESC-POS"),
}

#: Ports worth watching by default: the ones an Epson-aware app might try and
#: that BonBridge does not already answer itself.
DEFAULT_TCP = (631, 8008)
DEFAULT_UDP = (1900,)


def describe_port(port: int) -> str:
    name = PORT_NAMES.get(port)
    return f"{name[0]} ({port})" if name else str(port)


class _TcpHandler(socketserver.BaseRequestHandler):
    server: Any

    def handle(self) -> None:
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        connection: socket.socket = self.request
        connection.settimeout(3.0)
        data = b""
        try:
            data = connection.recv(8192)
        except (OSError, socket.timeout):
            pass
        port = self.server.server_address[1]
        self.server.owner.record(port, "tcp", peer, data)


class _ThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    owner: Any = None


class PortWatcher(threading.Thread):
    """One passive listener, TCP or UDP, on one port."""

    def __init__(self, owner: "PortWatch", port: int, protocol: str = "tcp", bind: str = "0.0.0.0"):
        super().__init__(name=f"watch-{protocol}-{port}", daemon=True)
        self.owner = owner
        self.port = port
        self.protocol = protocol
        self.bind = bind
        self.hits = 0
        self.last_error: Optional[str] = None
        self._server: Optional[_ThreadingTCPServer] = None
        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        if self.protocol == "udp":
            self._run_udp()
        else:
            self._run_tcp()

    def _run_tcp(self) -> None:
        try:
            server = _ThreadingTCPServer((self.bind, self.port), _TcpHandler)
            server.owner = self.owner
            self._server = server
        except OSError as exc:
            self.last_error = str(exc)
            log.info("Port watch cannot bind tcp/%s: %s", self.port, exc)
            return
        log.info("Watching tcp/%s (%s)", self.port, describe_port(self.port))
        try:
            server.serve_forever(poll_interval=0.5)
        except Exception as exc:  # noqa: BLE001
            if not self._stop_event.is_set():
                log.debug("Port watch tcp/%s stopped: %s", self.port, exc)
        finally:
            try:
                server.server_close()
            except Exception:  # noqa: BLE001
                pass
            self._server = None

    def _run_udp(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.bind, self.port))
            self._sock.settimeout(0.5)
        except OSError as exc:
            self.last_error = str(exc)
            log.info("Port watch cannot bind udp/%s: %s", self.port, exc)
            return
        log.info("Watching udp/%s (%s)", self.port, describe_port(self.port))
        while not self._stop_event.is_set():
            try:
                data, peer = self._sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                continue
            self.owner.record(self.port, "udp", f"{peer[0]}:{peer[1]}", data)
        try:
            self._sock.close()
        except OSError:
            pass

    def stop(self) -> None:
        self._stop_event.set()
        if self._server is not None:
            try:
                self._server.shutdown()
            except Exception:  # noqa: BLE001
                pass

    @property
    def listening(self) -> bool:
        if self.protocol == "udp":
            return self._sock is not None and self.last_error is None
        return self._server is not None and self.last_error is None


class PortWatch:
    """Owns a set of passive listeners and reports what they saw."""

    def __init__(
        self,
        probe_log: ProbeLog,
        tcp_ports: Optional[List[int]] = None,
        udp_ports: Optional[List[int]] = None,
        bind: str = "0.0.0.0",
    ):
        self.probe_log = probe_log
        self.bind = bind
        self.tcp_ports = list(tcp_ports if tcp_ports is not None else DEFAULT_TCP)
        self.udp_ports = list(udp_ports if udp_ports is not None else DEFAULT_UDP)
        self.watchers: List[PortWatcher] = []
        self._by_port: Dict[str, PortWatcher] = {}

    def record(self, port: int, protocol: str, peer: str, data: bytes) -> None:
        watcher = self._by_port.get(f"{protocol}/{port}")
        if watcher is not None:
            watcher.hits += 1
        label = PORT_NAMES.get(port, (f"{protocol}/{port}", ""))[0]
        preview = ""
        if data:
            text = data[:60].decode("ascii", "replace")
            preview = " " + "".join(ch if 32 <= ord(ch) < 127 else "." for ch in text)
        self.probe_log.add(
            f"{protocol}/{port}",
            peer,
            data,
            summary=f"{label} probe, {len(data)} B{preview}",
            note="watched only - not answered",
        )
        log.info("Probe on %s/%s from %s (%s bytes)", protocol, port, peer, len(data))

    def start(self) -> None:
        for port in self.tcp_ports:
            watcher = PortWatcher(self, port, "tcp", self.bind)
            self.watchers.append(watcher)
            self._by_port[f"tcp/{port}"] = watcher
            watcher.start()
        for port in self.udp_ports:
            watcher = PortWatcher(self, port, "udp", self.bind)
            self.watchers.append(watcher)
            self._by_port[f"udp/{port}"] = watcher
            watcher.start()

    def stop(self) -> None:
        for watcher in self.watchers:
            watcher.stop()
        self.watchers = []
        self._by_port = {}

    def snapshot(self) -> List[Dict[str, Any]]:
        return [
            {
                "port": watcher.port,
                "protocol": watcher.protocol,
                "label": PORT_NAMES.get(watcher.port, (f"{watcher.protocol}/{watcher.port}", ""))[0],
                "purpose": PORT_NAMES.get(
                    watcher.port, ("", "nur mitgehört / listening only")
                )[1],
                "listening": watcher.listening,
                "hits": watcher.hits,
                "error": watcher.last_error,
            }
            for watcher in self.watchers
        ]
