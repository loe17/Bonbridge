"""LPD/LPR on TCP 515 - the other printing protocol Epson interfaces speak.

The UB-E04 interface board offers LPR on port 515 alongside raw printing on
9100, so a POS or accounting system that looks for "a network printer" may
well knock on 515 first - and finding nothing there, decide that no printer
exists.  BonBridge now answers.

Two things come out of this:

* **Discovery.** Anything that probes port 515 gets a connection and a
  plausible queue status, and the attempt is written to the shared probe log
  so it is visible what asked and when.
* **Printing.** The protocol is small enough (RFC 1179 is about ten pages)
  that implementing "receive a job" properly costs little more than accepting
  the connection, so LPR clients can actually print.

Only the parts that matter for a receipt printer are implemented: receive job
(``\\x02``), send queue state (``\\x03``/``\\x04``) and remove jobs (``\\x05``,
answered but ignored - there is no persistent queue to remove things from).
The control file is parsed for the job and user name only; the data file goes
straight to the printer worker as ESC/POS, exactly like a job arriving on
9100.

References
----------
* RFC 1179 - Line Printer Daemon Protocol
* Epson UB-E04 Technical Reference Guide (LPR on 515, max 6 connections)
  https://files.support.epson.com/pdf/ube04_/ube04_trg.pdf
"""

from __future__ import annotations

import logging
import socket
import socketserver
import threading
from typing import Any, Callable, Dict, Optional

from .probes import ProbeLog

log = logging.getLogger(__name__)

LPD_PORT = 515

CMD_PRINT_WAITING = 0x01
CMD_RECEIVE_JOB = 0x02
CMD_QUEUE_STATE_SHORT = 0x03
CMD_QUEUE_STATE_LONG = 0x04
CMD_REMOVE_JOBS = 0x05

SUB_ABORT = 0x01
SUB_CONTROL_FILE = 0x02
SUB_DATA_FILE = 0x03

ACK = b"\x00"
NAK = b"\x01"

#: Refuse absurd jobs rather than filling the disk of a Pi Zero.
MAX_FILE_BYTES = 8 * 1024 * 1024


class _Handler(socketserver.BaseRequestHandler):
    server: Any  # set by socketserver

    def handle(self) -> None:  # noqa: C901 - the protocol is a flat state machine
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        connection: socket.socket = self.request
        connection.settimeout(30.0)
        owner: LpdServer = self.server.owner

        try:
            first = self._read_exact(connection, 1)
        except (OSError, ValueError):
            owner.probe_log.add("lpd", peer, b"", summary="connected, sent nothing")
            return
        if not first:
            owner.probe_log.add("lpd", peer, b"", summary="connected, sent nothing")
            return

        command = first[0]
        operand = self._read_line(connection)
        request = first + operand
        queue = operand.decode("ascii", "replace").strip()

        if command in (CMD_QUEUE_STATE_SHORT, CMD_QUEUE_STATE_LONG):
            status = owner.queue_status(queue)
            connection.sendall(status.encode("ascii", "replace"))
            owner.probe_log.add(
                "lpd", peer, request, answered=True,
                reply=status.encode("ascii", "replace"),
                summary=f"queue status '{queue or 'default'}'",
            )
            return

        if command == CMD_REMOVE_JOBS:
            connection.sendall(ACK)
            owner.probe_log.add(
                "lpd", peer, request, answered=True, summary="remove jobs (nothing queued)"
            )
            return

        if command != CMD_RECEIVE_JOB:
            connection.sendall(NAK)
            owner.probe_log.add(
                "lpd", peer, request, summary=f"unsupported LPD command 0x{command:02x}"
            )
            return

        # -- receive a job --------------------------------------------------
        connection.sendall(ACK)
        job_name = ""
        user = ""
        payload = b""
        while True:
            try:
                header = self._read_exact(connection, 1)
            except (OSError, ValueError):
                break
            if not header:
                break
            subcommand = header[0]
            line = self._read_line(connection)
            if subcommand == SUB_ABORT:
                connection.sendall(ACK)
                break
            if subcommand not in (SUB_CONTROL_FILE, SUB_DATA_FILE):
                connection.sendall(NAK)
                break

            parts = line.decode("ascii", "replace").strip().split(" ", 1)
            try:
                count = int(parts[0])
            except ValueError:
                connection.sendall(NAK)
                break
            if count < 0 or count > MAX_FILE_BYTES:
                connection.sendall(NAK)
                break
            connection.sendall(ACK)

            body = self._read_exact(connection, count)
            trailer = self._read_exact(connection, 1)  # expected 0x00
            connection.sendall(ACK)
            if trailer != b"\x00":
                log.debug("LPD: missing trailing NUL from %s", peer)

            if subcommand == SUB_CONTROL_FILE:
                for control_line in body.decode("ascii", "replace").splitlines():
                    if control_line[:1] == "J":
                        job_name = control_line[1:].strip()
                    elif control_line[:1] == "P":
                        user = control_line[1:].strip()
            else:
                payload = body

        if payload:
            label = f"LPR {len(payload)} B"
            if job_name:
                label += f" '{job_name[:32]}'"
            owner.deliver(payload, peer, label)
            owner.jobs += 1
        owner.probe_log.add(
            "lpd",
            peer,
            request,
            answered=True,
            summary=(
                f"print job, {len(payload)} B"
                + (f", user {user}" if user else "")
                + (f", queue '{queue}'" if queue else "")
            )
            if payload
            else "job started but no data received",
        )

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _read_exact(connection: socket.socket, count: int) -> bytes:
        chunks = []
        remaining = count
        while remaining > 0:
            chunk = connection.recv(min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    @staticmethod
    def _read_line(connection: socket.socket, limit: int = 1024) -> bytes:
        out = bytearray()
        while len(out) < limit:
            chunk = connection.recv(1)
            if not chunk or chunk == b"\n":
                break
            out += chunk
        return bytes(out)


class _ThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    owner: Any = None


class LpdServer(threading.Thread):
    """Accepts LPR connections on port 515 and forwards jobs to a printer."""

    def __init__(
        self,
        deliver: Callable[[bytes, str, str], None],
        probe_log: ProbeLog,
        *,
        bind: str = "0.0.0.0",
        port: int = LPD_PORT,
        queue_name: str = "BonBridge",
    ):
        super().__init__(name="lpd", daemon=True)
        self.deliver_callback = deliver
        self.probe_log = probe_log
        self.bind = bind
        self.port = port
        self.queue_name = queue_name
        self.jobs = 0
        self.last_error: Optional[str] = None
        self._server: Optional[_ThreadingTCPServer] = None
        self._stop_event = threading.Event()

    def deliver(self, data: bytes, peer: str, label: str) -> None:
        try:
            self.deliver_callback(data, peer, label)
        except Exception as exc:  # noqa: BLE001 - a bad job must not kill the server
            log.warning("LPD: cannot deliver job from %s: %s", peer, exc)

    def queue_status(self, queue: str) -> str:
        name = queue or self.queue_name
        return f"{name}: BonBridge is ready and printing\nno entries\n"

    def run(self) -> None:
        try:
            server = _ThreadingTCPServer((self.bind, self.port), _Handler)
            server.owner = self
            self._server = server
        except OSError as exc:
            self.last_error = str(exc)
            log.warning("LPD server cannot bind %s:%s: %s", self.bind, self.port, exc)
            return
        log.info("LPD server listening on %s:%s", self.bind, self.port)
        try:
            server.serve_forever(poll_interval=0.5)
        except Exception as exc:  # noqa: BLE001
            if not self._stop_event.is_set():
                log.warning("LPD server crashed: %s", exc)
        finally:
            try:
                server.server_close()
            except Exception:  # noqa: BLE001
                pass
            self._server = None

    def stop(self) -> None:
        self._stop_event.set()
        if self._server is not None:
            try:
                self._server.shutdown()
            except Exception:  # noqa: BLE001
                pass

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "port": self.port,
            "listening": self._server is not None and self.last_error is None,
            "jobs": self.jobs,
            "error": self.last_error,
        }
