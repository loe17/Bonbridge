"""RAW / JetDirect listener on TCP port 9100.

This is the interface POS applications talk to.  OrderAssist, for example,
only lets the user enter an IP address and then always connects to
``<ip>:9100`` - the port is not configurable in the app.  BonBridge therefore
listens on 9100 by default and, when several print groups are served by one
device, on 9100 of *several IP addresses* (see ``bind`` in the printer
configuration and ``bonbridge-ip@.service``).

Job segmentation: data is collected until the client closes the connection or
stays silent for ``idle_timeout`` seconds.  That covers both the
"connect - send - disconnect" pattern and applications that keep the socket
open between receipts.

References
----------
* RAW / JetDirect on port 9100 is a de-facto convention rather than a
  standard; the closest formal relative is RFC 1179 (LPD)
  https://datatracker.ietf.org/doc/html/rfc1179
* Counterpart on the client side: the CUPS ``socket`` backend
  https://www.cups.org/doc/network.html
* Full reference list: docs/en/09-references.md / docs/de/09-referenzen.md
"""

from __future__ import annotations

import logging
import socket
import socketserver
import threading
import time
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger(__name__)

#: Seconds of silence after which buffered data is treated as a finished job.
DEFAULT_IDLE_TIMEOUT = 0.4

#: Hard limit for a single job so a broken client cannot exhaust memory.
MAX_JOB_BYTES = 32 * 1024 * 1024


class _Handler(socketserver.BaseRequestHandler):
    server: "RawServer"  # type: ignore[assignment]

    def handle(self) -> None:  # noqa: C901 - explicit protocol loop
        server = self.server
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        server.note_connection(peer)
        log.info("[%s] RAW connection from %s", server.printer_id, peer)

        sock: socket.socket = self.request
        sock.settimeout(server.idle_timeout)
        buffer = bytearray()
        total = 0
        last_data = time.monotonic()

        def send_back(data: bytes) -> None:
            try:
                sock.sendall(data)
            except OSError:
                pass

        try:
            while not server.stopping:
                try:
                    chunk = sock.recv(65536)
                except socket.timeout:
                    if buffer and (time.monotonic() - last_data) >= server.idle_timeout:
                        total += len(buffer)
                        server.deliver(bytes(buffer), peer, send_back)
                        buffer.clear()
                    if server.connection_timeout and (
                        time.monotonic() - last_data
                    ) > server.connection_timeout:
                        break
                    continue
                except OSError as exc:
                    log.debug("[%s] socket error from %s: %s", server.printer_id, peer, exc)
                    break

                if not chunk:
                    break
                last_data = time.monotonic()
                buffer.extend(chunk)
                if len(buffer) > MAX_JOB_BYTES:
                    log.error(
                        "[%s] job from %s exceeds %s bytes - dropping connection",
                        server.printer_id,
                        peer,
                        MAX_JOB_BYTES,
                    )
                    buffer.clear()
                    break

            if buffer:
                total += len(buffer)
                server.deliver(bytes(buffer), peer, send_back)
        finally:
            log.info("[%s] RAW connection %s closed (%s bytes)", server.printer_id, peer, total)
            server.note_disconnect(peer)
            try:
                sock.close()
            except OSError:
                pass


class RawServer(socketserver.ThreadingTCPServer):
    """Threaded RAW listener bound to one address for one printer."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        printer_id: str,
        bind: str,
        port: int,
        deliver: Callable[[bytes, str, Callable[[bytes], None]], None],
        *,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
        connection_timeout: float = 0.0,
        max_connections: int = 8,
    ):
        self.printer_id = printer_id
        self.bind_address = bind
        self.port = port
        self._deliver = deliver
        self.idle_timeout = idle_timeout
        self.connection_timeout = connection_timeout
        self.max_connections = max_connections
        self.stopping = False

        self._conn_lock = threading.Lock()
        self.active_connections: List[str] = []
        self.total_connections = 0
        self.last_connection_at: Optional[float] = None
        self.last_peer: str = ""

        super().__init__((bind, port), _Handler, bind_and_activate=False)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_bind()
        self.server_activate()
        log.info("[%s] RAW listener on %s:%s", printer_id, bind, port)

    # -- bookkeeping -------------------------------------------------------

    def note_connection(self, peer: str) -> None:
        with self._conn_lock:
            self.active_connections.append(peer)
            self.total_connections += 1
            self.last_connection_at = time.time()
            self.last_peer = peer

    def note_disconnect(self, peer: str) -> None:
        with self._conn_lock:
            if peer in self.active_connections:
                self.active_connections.remove(peer)

    def deliver(self, data: bytes, peer: str, send_back: Callable[[bytes], None]) -> None:
        self._deliver(data, peer, send_back)

    def snapshot(self) -> Dict[str, Any]:
        with self._conn_lock:
            return {
                "bind": self.bind_address,
                "port": self.port,
                "active_connections": list(self.active_connections),
                "total_connections": self.total_connections,
                "last_connection_at": self.last_connection_at,
                "last_peer": self.last_peer,
            }

    def shutdown_now(self) -> None:
        self.stopping = True
        try:
            self.shutdown()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.server_close()
        except Exception:  # noqa: BLE001
            pass


class RawListenerSupervisor(threading.Thread):
    """Keeps a RAW listener alive even if its IP address appears late.

    When several print groups are served from one machine each printer binds
    to its own IP alias.  Those aliases may only exist after the network is
    fully up, so binding is retried instead of failing at start-up.
    """

    def __init__(
        self,
        printer_id: str,
        bind: str,
        port: int,
        deliver: Callable[[bytes, str, Callable[[bytes], None]], None],
        **options: Any,
    ):
        super().__init__(name=f"raw-{printer_id}", daemon=True)
        self.printer_id = printer_id
        self.bind = bind
        self.port = port
        self.deliver = deliver
        self.options = options
        self.server: Optional[RawServer] = None
        self.last_error: Optional[str] = None
        self._stop = threading.Event()

    def run(self) -> None:
        delay = 1.0
        while not self._stop.is_set():
            try:
                self.server = RawServer(
                    self.printer_id, self.bind, self.port, self.deliver, **self.options
                )
                self.last_error = None
                delay = 1.0
            except OSError as exc:
                self.last_error = f"cannot bind {self.bind}:{self.port}: {exc}"
                log.warning("[%s] %s (retrying)", self.printer_id, self.last_error)
                self._stop.wait(delay)
                delay = min(delay * 2, 30.0)
                continue

            try:
                self.server.serve_forever(poll_interval=0.5)
            except Exception as exc:  # noqa: BLE001
                log.warning("[%s] RAW listener crashed: %s", self.printer_id, exc)
            finally:
                server = self.server
                self.server = None
                if server is not None:
                    server.shutdown_now()
            if not self._stop.is_set():
                self._stop.wait(1.0)

    def stop(self) -> None:
        self._stop.set()
        if self.server is not None:
            self.server.shutdown_now()

    def snapshot(self) -> Dict[str, Any]:
        if self.server is not None:
            data = self.server.snapshot()
            data["listening"] = True
            data["error"] = None
            return data
        return {
            "bind": self.bind,
            "port": self.port,
            "listening": False,
            "error": self.last_error,
            "active_connections": [],
            "total_connections": 0,
            "last_connection_at": None,
            "last_peer": "",
        }
